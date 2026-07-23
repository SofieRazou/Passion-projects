clear;
clc;

%% Vehicle and simulation settings
time_step = 0.01;   % Sampling period [s]
duration = 30;      % Data collection duration [s]

u = 30.0;           % Vehicle velocity [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial x-position [m]
y = 0.0;            % Initial y-position [m]

%% Shared-memory file
filePath = ...
    "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

if ~isfile(filePath)
    error("Shared-memory file not found: %s", filePath);
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

% Store x, y and z coordinates
waypoints = zeros(maxSamples, 3, "double");

cnt = 0;
startTime = tic;

%% Collect the vehicle trajectory
while toc(startTime) < duration

    validSample = false;

    %% Read one complete shared-memory sample
    while ~validSample
        sequenceBefore = sharedMemory.Data.Sequence;

        % Odd sequence means Python is currently writing
        if mod(sequenceBefore, 2) ~= 0
            pause(0.0001);
            continue;
        end

        newCommands = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        % Ensure the sample was not changed during the read
        validSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;
    end

    %% Convert commands to double
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected 2 values from shared_data.bin, received %d.", ...
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

    %% Convert returned coordinates to double
    x = double(xNew);
    y = double(yNew);

    %% Store the waypoint
    cnt = cnt + 1;

    if cnt > size(waypoints, 1)
        waypoints = [ ...
            waypoints; ...
            zeros(1000, 3, "double") ...
        ];
    end

    % Driving-scenario waypoints use [x, y, z]
    waypoints(cnt, :) = double([x, y, 0.0]);

    %% Display current values
    fprintf( ...
        "delta = %.4f, theta = %.4f, x = %.4f, y = %.4f\n", ...
        delta, thetaCommand, x, y);

    pause(time_step);
end

%% Remove unused waypoint rows
waypoints = double(waypoints(1:cnt, :));

%% Remove invalid rows
validRows = all(isfinite(waypoints), 2);
waypoints = waypoints(validRows, :);

if size(waypoints, 1) < 2
    error("At least two valid waypoints are required.");
end

%% Remove consecutive duplicate waypoints
positionChange = [ ...
    true; ...
    any(diff(waypoints(:, 1:2), 1, 1) ~= 0, 2) ...
];

waypoints = waypoints(positionChange, :);

if size(waypoints, 1) < 2
    error("The generated trajectory contains fewer than two unique points.");
end

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

%% Display the collected trajectory
figure;

plot(waypoints(:, 1), waypoints(:, 2), "LineWidth", 1.5);

xlabel("x [m]");
ylabel("y [m]");
title("Collected vehicle trajectory");

grid on;
axis equal;

%% Display the driving scenario
figure;
scenarioPlot = plot(scenario);

title("Driving scenario");

%% Run the scenario
restart(scenario);

while advance(scenario)
    pause(time_step);
end
