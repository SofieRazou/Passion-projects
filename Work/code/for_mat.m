clear;
clc;
close all;

%% Vehicle settings
time_step = 0.01;   % Expected Python sampling period [s]

u = 30.0;           % Vehicle velocity [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial x-position [m]
y = 0.0;            % Initial y-position [m]

%% Shared-memory file
filePath = ...
    "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

fprintf("Waiting for shared_data.bin...\n");

while ~isfile(filePath)
    pause(0.1);
end

%% Wait until the file has the expected size
fileInfo = dir(filePath);

while fileInfo.bytes ~= 24
    pause(0.1);
    fileInfo = dir(filePath);
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

%% Create the driving scenario immediately
scenario = drivingScenario( ...
    "SampleTime", time_step);

%% Create a road
roadCenters = [ ...
      0, 0, 0; ...
    500, 0, 0 ...
];

road( ...
    scenario, ...
    roadCenters, ...
    "Lanes", lanespec(2));

%% Create the vehicle actor
egoCar = vehicle( ...
    scenario, ...
    "ClassID", 1, ...
    "Position", double([x, y, 0]), ...
    "Yaw", 0);

%% Open the driving scenario immediately
scenarioFigure = figure( ...
    "Name", "Real-Time Driving Scenario", ...
    "NumberTitle", "off");

scenarioAxes = axes( ...
    "Parent", scenarioFigure);

plot( ...
    scenario, ...
    "Parent", scenarioAxes, ...
    "Waypoints", "off", ...
    "RoadCenters", "off");

title(scenarioAxes, "Real-Time Driving Scenario");
xlabel(scenarioAxes, "x [m]");
ylabel(scenarioAxes, "y [m]");

axis(scenarioAxes, "equal");
grid(scenarioAxes, "on");

%% Create the real-time trajectory plot
trajectoryFigure = figure( ...
    "Name", "Real-Time Vehicle Trajectory", ...
    "NumberTitle", "off");

trajectoryAxes = axes( ...
    "Parent", trajectoryFigure);

trajectoryLine = animatedline( ...
    trajectoryAxes, ...
    "LineWidth", 1.5);

xlabel(trajectoryAxes, "x [m]");
ylabel(trajectoryAxes, "y [m]");
title(trajectoryAxes, "Real-Time Vehicle Trajectory");

axis(trajectoryAxes, "equal");
grid(trajectoryAxes, "on");

%% Preallocate trajectory storage
waypoints = zeros(1000, 3, "double");

cnt = 0;
lastSequence = uint64(0);

fprintf("Driving scenario opened.\n");
fprintf("Waiting for Python samples...\n");

%% Real-time reading and visualization loop
while isvalid(scenarioFigure) && isvalid(trajectoryFigure)

    validNewSample = false;

    %% Wait for one complete new Python sample
    while ~validNewSample

        if ~isvalid(scenarioFigure) || ...
                ~isvalid(trajectoryFigure)
            break;
        end

        sequenceBefore = sharedMemory.Data.Sequence;

        % Sequence zero means Python has not published anything yet
        if sequenceBefore == 0
            pause(0.0001);
            drawnow limitrate;
            continue;
        end

        % Odd sequence means Python is currently writing
        if mod(sequenceBefore, 2) ~= 0
            pause(0.0001);
            continue;
        end

        % Ignore a sample that was already processed
        if sequenceBefore == lastSequence
            pause(0.0001);
            drawnow limitrate;
            continue;
        end

        newCommands = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        % Accept only an unchanged completed sample
        validNewSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;

        if validNewSample
            lastSequence = sequenceAfter;
        end
    end

    if ~isvalid(scenarioFigure) || ...
            ~isvalid(trajectoryFigure)
        break;
    end

    %% Convert commands to MATLAB doubles
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        warning( ...
            "Expected 2 values, but received %d.", ...
            numel(commands));

        continue;
    end

    %% Extract Python commands
    delta = double(commands(1));
    thetaCommand = double(commands(2));

    if ~isfinite(delta) || ~isfinite(thetaCommand)
        warning("Invalid command received. Sample ignored.");
        continue;
    end

    %% Calculate the new vehicle position
    [xNew, yNew] = run_driving_venv( ...
        delta, ...
        thetaCommand, ...
        u, ...
        L, ...
        x, ...
        y, ...
        time_step);

    x = double(xNew);
    y = double(yNew);

    if ~isfinite(x) || ~isfinite(y)
        warning("Invalid vehicle position. Sample ignored.");
        continue;
    end

    %% Store x and y as double trajectory values
    cnt = cnt + 1;

    if cnt > size(waypoints, 1)
        waypoints = [ ...
            waypoints; ...
            zeros(1000, 3, "double") ...
        ];
    end

    waypoints(cnt, :) = double([x, y, 0.0]);

    %% Update the car actor in real time
    egoCar.Position = double([x, y, 0.0]);

    % MATLAB driving-scenario Yaw is in degrees
    egoCar.Yaw = double(rad2deg(thetaCommand));

    %% Update the live trajectory
    addpoints(trajectoryLine, x, y);

    %% Keep the trajectory plot centered around the car
    viewDistance = 30;

    xlim(trajectoryAxes, ...
        [x - viewDistance, x + viewDistance]);

    ylim(trajectoryAxes, ...
        [y - viewDistance, y + viewDistance]);

    %% Keep the driving-scenario view around the car
    xlim(scenarioAxes, ...
        [x - viewDistance, x + viewDistance]);

    ylim(scenarioAxes, ...
        [y - viewDistance, y + viewDistance]);

    %% Refresh both figures
    drawnow limitrate;

    %% Display current values
    fprintf( ...
        "sequence = %d, delta = %.5f, theta = %.5f, " + ...
        "x = %.5f, y = %.5f\n", ...
        lastSequence, ...
        delta, ...
        thetaCommand, ...
        x, ...
        y);
end

%% Keep only the recorded trajectory
waypoints = double(waypoints(1:cnt, :));

fprintf("Real-time visualization stopped.\n");
fprintf("Recorded %d trajectory points.\n", cnt);
