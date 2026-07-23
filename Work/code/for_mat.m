clear;
clc;
close all;

%% ============================================================
% Vehicle and simulation settings
% =============================================================

time_step = 0.01;   % Expected Python update period [s]
u = 30.0;           % Vehicle speed [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial vehicle x-position [m]
y = 0.0;            % Initial vehicle y-position [m]
yaw = 0.0;          % Initial vehicle heading [rad]

%% ============================================================
% Shared-memory file
% =============================================================

filePath = ...
    "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

fprintf("Waiting for shared-memory file...\n");

while ~isfile(filePath)
    pause(0.1);
end

%% Wait until Python creates the complete 24-byte file

fileInfo = dir(filePath);

while isempty(fileInfo) || fileInfo.bytes ~= 24
    pause(0.1);
    fileInfo = dir(filePath);
end

fprintf("Shared-memory file found.\n");

%% ============================================================
% Map the Python binary file
%
% Binary layout:
%   Bytes 1-8:   uint64 sequence
%   Bytes 9-16:  double delta
%   Bytes 17-24: double thetaCommand
% =============================================================

sharedMemory = memmapfile( ...
    filePath, ...
    "Writable", false, ...
    "Format", { ...
        "uint64", [1 1], "Sequence"; ...
        "double", [1 2], "Values" ...
    });

%% ============================================================
% Load the already existing driving scenario
% =============================================================

% Replace createExistingScenario with the name of the function
% exported from Driving Scenario Designer.
%
% The exported function should return:
%   scenario - the drivingScenario object
%   egoCar   - the vehicle actor that should be controlled

[scenario, egoCar] = createExistingScenario();

scenario.SampleTime = time_step;

%% Use the actor's initial scenario position

initialPosition = double(egoCar.Position);

x = initialPosition(1);
y = initialPosition(2);

% Driving Scenario stores yaw in degrees
yaw = deg2rad(double(egoCar.Yaw));

fprintf("Existing scenario loaded.\n");
fprintf( ...
    "Initial position: x = %.3f m, y = %.3f m, yaw = %.3f deg\n", ...
    x, ...
    y, ...
    egoCar.Yaw);

%% ============================================================
% Open the existing scenario
% =============================================================

scenarioFigure = figure( ...
    "Name", "Real-Time Existing Driving Scenario", ...
    "NumberTitle", "off", ...
    "Color", "white");

scenarioAxes = axes( ...
    "Parent", scenarioFigure);

plot( ...
    scenario, ...
    "Parent", scenarioAxes, ...
    "Waypoints", "off", ...
    "RoadCenters", "off");

title( ...
    scenarioAxes, ...
    "Real-Time Python-Controlled Vehicle");

xlabel(scenarioAxes, "x [m]");
ylabel(scenarioAxes, "y [m]");

axis(scenarioAxes, "equal");
grid(scenarioAxes, "on");

%% ============================================================
% Create a live trajectory trace
% =============================================================

hold(scenarioAxes, "on");

trajectoryLine = animatedline( ...
    scenarioAxes, ...
    "LineWidth", 1.5, ...
    "DisplayName", "Generated trajectory");

addpoints(trajectoryLine, x, y);

%% ============================================================
% Allocate trajectory storage
% =============================================================

allocationSize = 10000;

generatedWaypoints = zeros( ...
    allocationSize, ...
    3, ...
    "double");

generatedTime = zeros( ...
    allocationSize, ...
    1, ...
    "double");

generatedDelta = zeros( ...
    allocationSize, ...
    1, ...
    "double");

generatedYaw = zeros( ...
    allocationSize, ...
    1, ...
    "double");

sampleCount = 0;

%% ============================================================
% Synchronization variables
% =============================================================

lastSequence = uint64(0);
simulationStartTime = tic;

fprintf("Driving scenario opened.\n");
fprintf("Waiting for Python commands...\n");
fprintf("Close the scenario window to stop MATLAB.\n");

%% ============================================================
% Real-time loop
% =============================================================

while isvalid(scenarioFigure)

    validNewSample = false;

    %% Wait for one complete, new Python sample

    while ~validNewSample

        if ~isvalid(scenarioFigure)
            break;
        end

        sequenceBefore = sharedMemory.Data.Sequence;

        % Sequence zero means Python has not written a sample yet
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

        % Ignore the previous sample
        if sequenceBefore == lastSequence
            pause(0.0001);
            drawnow limitrate;
            continue;
        end

        newValues = sharedMemory.Data.Values;

        sequenceAfter = sharedMemory.Data.Sequence;

        % The sample is valid only when the sequence remained unchanged
        % and is even after reading the values
        validNewSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;

        if validNewSample
            lastSequence = sequenceAfter;
        end
    end

    if ~isvalid(scenarioFigure)
        break;
    end

    %% ========================================================
    % Read the commands
    % =========================================================

    commands = double(newValues(:).');

    if numel(commands) ~= 2
        warning( ...
            "Expected two commands but received %d.", ...
            numel(commands));

        continue;
    end

    delta = commands(1);
    thetaCommand = commands(2);

    if ~isfinite(delta) || ~isfinite(thetaCommand)
        warning("Invalid command received. Sample ignored.");
        continue;
    end

    %% ========================================================
    % Calculate the next vehicle position
    % =========================================================

    [xNew, yNew] = run_driving_venv( ...
        delta, ...
        thetaCommand, ...
        u, ...
        L, ...
        x, ...
        y, ...
        time_step);

    xNew = double(xNew);
    yNew = double(yNew);

    if ~isfinite(xNew) || ~isfinite(yNew)
        warning("Invalid vehicle position calculated.");
        continue;
    end

    x = xNew;
    y = yNew;

    %% Choose which value represents vehicle orientation
    %
    % If thetaCommand already represents the global vehicle heading,
    % use it directly:
    yaw = thetaCommand;
    %
    % If thetaCommand is not the heading, but delta is the steering
    % wheel angle, replace the line above with:
    %
    % yaw = yaw + (u / L) * tan(delta) * time_step;

    %% ========================================================
    % Store the generated trajectory
    % =========================================================

    sampleCount = sampleCount + 1;

    if sampleCount > size(generatedWaypoints, 1)

        generatedWaypoints = [ ...
            generatedWaypoints; ...
            zeros(allocationSize, 3, "double") ...
        ];

        generatedTime = [ ...
            generatedTime; ...
            zeros(allocationSize, 1, "double") ...
        ];

        generatedDelta = [ ...
            generatedDelta; ...
            zeros(allocationSize, 1, "double") ...
        ];

        generatedYaw = [ ...
            generatedYaw; ...
            zeros(allocationSize, 1, "double") ...
        ];
    end

    generatedWaypoints(sampleCount, :) = [x, y, 0.0];
    generatedTime(sampleCount) = toc(simulationStartTime);
    generatedDelta(sampleCount) = delta;
    generatedYaw(sampleCount) = yaw;

    %% ========================================================
    % Import the current trajectory point into the existing actor
    % =========================================================

    egoCar.Position = double([x, y, 0.0]);

    % Driving Scenario uses degrees for Yaw
    egoCar.Yaw = double(rad2deg(yaw));

    egoCar.Velocity = double([ ...
        u * cos(yaw), ...
        u * sin(yaw), ...
        0.0 ...
    ]);

    %% ========================================================
    % Update the live trajectory trace
    % =========================================================

    addpoints(trajectoryLine, x, y);

    %% ========================================================
    % Keep the camera centered around the vehicle
    % =========================================================

    viewDistanceBehind = 20;
    viewDistanceAhead = 50;
    viewDistanceSide = 30;

    xlim( ...
        scenarioAxes, ...
        [ ...
            x - viewDistanceBehind, ...
            x + viewDistanceAhead ...
        ]);

    ylim( ...
        scenarioAxes, ...
        [ ...
            y - viewDistanceSide, ...
            y + viewDistanceSide ...
        ]);

    %% ========================================================
    % Refresh the scenario
    % =========================================================

    drawnow limitrate;

    %% Display current state occasionally

    if mod(sampleCount, 10) == 0
        fprintf( ...
            "Sample: %6d | delta: %8.4f rad | " + ...
            "yaw: %8.3f deg | x: %8.3f | y: %8.3f\n", ...
            sampleCount, ...
            delta, ...
            rad2deg(yaw), ...
            x, ...
            y);
    end
end

%% ============================================================
% Trim unused trajectory storage
% =============================================================

generatedWaypoints = ...
    generatedWaypoints(1:sampleCount, :);

generatedTime = ...
    generatedTime(1:sampleCount);

generatedDelta = ...
    generatedDelta(1:sampleCount);

generatedYaw = ...
    generatedYaw(1:sampleCount);

%% ============================================================
% Save the recorded trajectory
% =============================================================

trajectoryData = table( ...
    generatedTime, ...
    generatedWaypoints(:, 1), ...
    generatedWaypoints(:, 2), ...
    generatedWaypoints(:, 3), ...
    generatedDelta, ...
    generatedYaw, ...
    "VariableNames", { ...
        "Time", ...
        "X", ...
        "Y", ...
        "Z", ...
        "SteeringAngle", ...
        "Yaw" ...
    });

save( ...
    "generated_real_time_trajectory.mat", ...
    "generatedWaypoints", ...
    "generatedTime", ...
    "generatedDelta", ...
    "generatedYaw", ...
    "trajectoryData");

fprintf("\nReal-time scenario stopped.\n");
fprintf("Recorded trajectory points: %d\n", sampleCount);
fprintf( ...
    "Trajectory saved to generated_real_time_trajectory.mat\n");
