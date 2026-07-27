clear;
clc;
close all;

%% Vehicle settings
time_step = 0.01;   % Expected Python sampling period [s]

u = 30.0;           % Vehicle velocity [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial x-position [m]
y = 0.0;            % Initial y-position [m]
z_height = 0.5;     % Heights offset [m] to prevent 3D terrain collision errors

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

%% Create the driving scenario
scenario = drivingScenario( ...
    "SampleTime", time_step);

%% Create a straight road
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
    "Position", double([x, y, z_height]), ...
    "Yaw", 0);

%% Open the driving scenario 2D/3D visualization figures
scenarioFigure = figure( ...
    "Name", "Real-Time Dynamic Driving Scenario", ...
    "NumberTitle", "off");

scenarioAxes = axes( ...
    "Parent", scenarioFigure);

plot( ...
    scenario, ...
    "Parent", scenarioAxes, ...
    "Waypoints", "off", ...
    "RoadCenters", "off");

title(scenarioAxes, "Real-Time Dynamic Driving Scenario");
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

%% Preallocate trajectory, heading & steering angle storage
waypoints = zeros(1000, 3, "double");
deltas    = zeros(1000, 1, "double");  % Steering angle log
yaws      = zeros(1000, 1, "double");  % Heading angle log (deg)

cnt = 0;
lastSequence = uint64(0);

fprintf("Driving scenario initialized.\n");
fprintf("Streaming Python samples live into scenario via advance()...\n");

%% Dynamic Real-Time Reading & Scenario Frame Engine Loop
while isvalid(scenarioFigure) && isvalid(trajectoryFigure)

    validNewSample = false;

    %% Wait for one complete new Python sample
    while ~validNewSample

        if ~isvalid(scenarioFigure) || ~isvalid(trajectoryFigure)
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

    if ~isvalid(scenarioFigure) || ~isvalid(trajectoryFigure)
        break;
    end

    %% Convert commands to MATLAB doubles
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        warning("Expected 2 values, but received %d.", numel(commands));
        continue;
    end

    %% Extract Python commands
    delta = double(commands(1));
    thetaCommand = double(commands(2));

    if ~isfinite(delta) || ~isfinite(thetaCommand)
        warning("Invalid command received. Sample ignored.");
        continue;
    end

    %% Calculate the new dynamic vehicle position
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

    %% Log x, y, z, delta, and yaw values
    cnt = cnt + 1;

    % Dynamically expand buffer memory if limit is reached
    if cnt > size(waypoints, 1)
        waypoints = [waypoints; zeros(1000, 3, "double")];
        deltas    = [deltas; zeros(1000, 1, "double")];
        yaws      = [yaws; zeros(1000, 1, "double")];
    end

    waypoints(cnt, :) = double([x, y, z_height]);
    deltas(cnt, 1)    = delta;
    yaws(cnt, 1)      = rad2deg(thetaCommand); % Yaw in degrees

    %% Dynamically Update Vehicle Pose in the Driving Engine
    egoCar.Position = double([x, y, z_height]);
    egoCar.Yaw      = double(rad2deg(thetaCommand));

    %% Advance Scenario Frame Engine
    % Moves the 3D vehicle actor forward dynamically frame-by-frame
    advance(scenario);

    %% Update live trajectory plot line
    addpoints(trajectoryLine, x, y);

    %% Keep plot camera centered live on the moving car
    viewDistance = 30;

    xlim(trajectoryAxes, [x - viewDistance, x + viewDistance]);
    ylim(trajectoryAxes, [y - viewDistance, y + viewDistance]);

    xlim(scenarioAxes, [x - viewDistance, x + viewDistance]);
    ylim(scenarioAxes, [y - viewDistance, y + viewDistance]);

    %% Force graphics refresh per step
    drawnow limitrate;

    %% Print sample info
    fprintf( ...
        "seq = %d, delta = %.5f rad, theta = %.5f rad, x = %.2f, y = %.2f\n", ...
        lastSequence, delta, thetaCommand, x, y);
end

%% Post-Processing: Package logged trajectory into base workspace
if cnt > 0
    raw_waypoints = double(waypoints(1:cnt, :));
    raw_deltas    = double(deltas(1:cnt, 1));
    raw_yaws      = double(yaws(1:cnt, 1));

    num_points = size(raw_waypoints, 1);
    t = (0:num_points-1)' * time_step;

    % Create standard timeseries objects
    waypoints_ts = timeseries(raw_waypoints, t);
    deltas_ts    = timeseries(raw_deltas, t);
    
    pos_ts = waypoints_ts;
    orient_matrix = [zeros(num_points, 2), raw_yaws];
    orient_ts = timeseries(orient_matrix, t);

    % Assign to workspace for inspection or optional post-analysis
    assignin('base', 'pos_ts', pos_ts);
    assignin('base', 'orient_ts', orient_ts);
    assignin('base', 'deltas_ts', deltas_ts);

    fprintf("\nLive streaming session finished.\n");
    fprintf("Logged %d trajectory points dynamically.\n", cnt);
else
    warning("No valid samples were captured.");
end
