clear;
clc;

%% Vehicle settings
time_step = 0.01;   % Expected Python sampling period [s]
duration = 30;      % Number of seconds of new data to collect

u = 30.0;           % Vehicle velocity [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial x-position [m]
y = 0.0;            % Initial y-position [m]

%% Shared-memory file
filePath = ...
    "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

fprintf("Waiting for the Python shared-memory file...\n");

while ~isfile(filePath)
    pause(0.1);
end

%% Shared-memory layout
% Bytes 1-8:   uint64 sequence counter
% Bytes 9-16:  double steering command
% Bytes 17-24: double heading command

sharedMemory = memmapfile( ...
    filePath, ...
    "Writable", false, ...
    "Format", { ...
        "uint64", [1 1], "Sequence"; ...
        "double", [1 2], "Values" ...
    });

%% Preallocate waypoint matrix
maxSamples = ceil(duration / time_step);

% Driving-scenario waypoints use [x, y, z]
waypoints = zeros(maxSamples, 3, "double");

cnt = 0;
lastSequence = uint64(0);
collectionStarted = false;

fprintf("Waiting for Python to publish the first sample...\n");

%% Read live samples from Python
while true

    %% Stop after the requested duration of live data
    if collectionStarted && toc(collectionStartTime) >= duration
        break;
    end

    validNewSample = false;

    %% Wait for a complete and new sample
    while ~validNewSample

        sequenceBefore = sharedMemory.Data.Sequence;

        % Sequence zero means Python has not published data yet
        if sequenceBefore == 0
            pause(0.0001);
            continue;
        end

        % Odd sequence means Python is currently writing
        if mod(sequenceBefore, 2) ~= 0
            pause(0.0001);
            continue;
        end

        % Wait until Python publishes a new sample
        if sequenceBefore == lastSequence
            pause(0.0001);
            continue;
        end

        newCommands = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        % Accept only a complete and unchanged sample
        validNewSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;

        if validNewSample
            lastSequence = sequenceAfter;
        end
    end

    %% Start timing when the first valid sample arrives
    if ~collectionStarted
        collectionStartTime = tic;
        collectionStarted = true;

        fprintf("First Python sample received.\n");
    end

    %% Convert commands to double
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected 2 commands, but received %d.", ...
            numel(commands));
    end

    %% Extract commands
    delta = double(commands(1));
    thetaCommand = double(commands(2));

    %% Run one vehicle-model step
    [xNew, yNew] = run_driving_venv( ...
        delta, ...
        thetaCommand, ...
        u, ...
        L, ...
        x, ...
        y, ...
        time_step);

    %% Update vehicle position
    x = double(xNew);
    y = double(yNew);

    if ~isfinite(x) || ~isfinite(y)
        warning("Invalid position received. Sample ignored.");
        continue;
    end

    %% Store the position as a double waypoint
    cnt = cnt + 1;

    if cnt > size(waypoints, 1)
        waypoints = [ ...
            waypoints; ...
            zeros(1000, 3, "double") ...
        ];
    end

    waypoints(cnt, :) = double([x, y, 0.0]);

    fprintf( ...
        "sequence = %d, delta = %.5f, theta = %.5f, " + ...
        "x = %.5f, y = %.5f\n", ...
        lastSequence, ...
        delta, ...
        thetaCommand, ...
        x, ...
        y);
end

%% Remove unused waypoint rows
waypoints = double(waypoints(1:cnt, :));

if size(waypoints, 1) < 2
    error("At least two valid waypoints are required.");
end

%% Remove invalid waypoints
validRows = all(isfinite(waypoints), 2);
waypoints = waypoints(validRows, :);

%% Remove consecutive duplicate positions
positionDifference = diff(waypoints(:, 1:2), 1, 1);

uniqueRows = [ ...
    true; ...
    any(abs(positionDifference) > 1e-9, 2) ...
];

waypoints = waypoints(uniqueRows, :);

if size(waypoints, 1) < 2
    error("The trajectory contains fewer than two unique positions.");
end

%% Plot the collected trajectory
figure;

plot( ...
    waypoints(:, 1), ...
    waypoints(:, 2), ...
    "LineWidth", ...
    1.5);

xlabel("x [m]");
ylabel("y [m]");
title("Collected vehicle trajectory");

grid on;
axis equal;

%% Create the driving scenario
scenario = drivingScenario( ...
    "SampleTime", time_step);

%% Create the car actor
egoCar = vehicle( ...
    scenario, ...
    "ClassID", 1, ...
    "Position", waypoints(1, :));

%% Assign the collected waypoints to the car
trajectory(egoCar, waypoints, u);

%% Open a scenario figure
figure;
plot(scenario);
title("Driving scenario");

%% Play the scenario
restart(scenario);

while advance(scenario)
    drawnow limitrate;
    pause(time_step);
end

fprintf("Driving scenario finished.\n");
