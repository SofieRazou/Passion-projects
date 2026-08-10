clear
close all
clc

%% =============================================================
%                  KNOWN PHYSICAL PARAMETERS
% =============================================================
J = 0.0103; % Motor inertia [kg*m^2]

%% =============================================================
%                   LOAD AND PREPARE DATA
% =============================================================
if ~exist('exp_sorted.mat', 'file')
    error('exp_sorted.mat not found! Run the extraction script first.');
end

load('exp_sorted.mat'); 

% Identify individual segments based on time resets (where time jumps back to near 0)
time_vec   = exp_sorted(:, 3);
seg_breaks = find(diff(time_vec) < 0);
start_indices = [1; seg_breaks + 1];
end_indices   = [seg_breaks; length(time_vec)];

num_total_segments = length(start_indices);
fprintf('Found %d individual segments to analyze.\n\n', num_total_segments);

% Preallocate arrays for summary results
b_est_all   = zeros(num_total_segments, 1);
k_est_all   = zeros(num_total_segments, 1);
fit_tf_all  = zeros(num_total_segments, 1);
fit_ss_all  = zeros(num_total_segments, 1);

%% =============================================================
%              LOOP THROUGH EACH EXPERIMENT SEGMENT
% =============================================================
for s = 1:num_total_segments
    % Extract current segment slices
    idx = start_indices(s):end_indices(s);
    seg_angle = exp_sorted(idx, 1); % Column 1: Angle (deg)
    seg_load  = exp_sorted(idx, 2); % Column 2: Measured Torque (Nm)
    seg_time  = exp_sorted(idx, 3); % Column 3: Time (s)
    
    % Compute sample time Ts for this specific segment
    Ts = mean(diff(seg_time));
    
    % Zero-mean signals & convert angle to radians
    u = seg_load(:) - mean(seg_load(:));
    y = deg2rad(seg_angle(:) - mean(seg_angle(:)));
    
    % Create iddata object for the segment
    data_id = iddata(y, u, Ts);
    data_id.InputName  = {'Measured torque'};
    data_id.OutputName = {'Encoder angle'};
    data_id.InputUnit  = {'Nm'};
    data_id.OutputUnit = {'rad'};
    data_id.ExperimentName = {sprintf('Segment_%d', s)};
    
    % ----------------------------------------------------------
    % 1st ID METHOD: Transfer Function Estimation (2 poles, 0 zeros)
    % ----------------------------------------------------------
    Gest = tfest(data_id, 2, 0);
    
    % Extract physical parameters: b = a1 * J , k = a0 * J
    [~, den] = tfdata(Gest, 'v');
    b_est = den(2) * J;
    k_est = den(3) * J;
    
    % ----------------------------------------------------------
    % 2nd ID METHOD: State-Space Estimation (2 states)
    % ----------------------------------------------------------
    Gss = ssest(data_id, 2);
    
    % Calculate fits
    [~, fit_tf] = compare(data_id, Gest);
    [~, fit_ss] = compare(data_id, Gss);
    
    % Store metrics
    b_est_all(s)  = b_est;
    k_est_all(s)  = k_est;
    fit_tf_all(s) = fit_tf;
    fit_ss_all(s) = fit_ss;
    
    % Plot response for this segment
    figure('Name', sprintf('Segment %d Fit', s));
    compare(data_id, Gest, Gss);
    grid on;
    title(sprintf('Segment %d: Fit TF = %.1f%%, SS = %.1f%%', s, fit_tf, fit_ss));
    set(findall(gcf, 'Type', 'Line'), 'LineWidth', 1.5);
    drawnow;
end

%% =============================================================
%                   PRINT SUMMARY RESULTS
% =============================================================
Segment_ID = (1:num_total_segments)';
SummaryTable = table(Segment_ID, b_est_all, k_est_all, fit_tf_all, fit_ss_all, ...
    'VariableNames', {'Segment', 'Damping_b_Nms_rad', 'Stiffness_k_Nm_rad', 'TF_Fit_Percent', 'SS_Fit_Percent'});

disp('========================================================================');
disp('                       SYSTEM IDENTIFICATION RESULTS                   ');
disp('========================================================================');
disp(SummaryTable);

% Overall Averages
fprintf('\n--- OVERALL AVERAGES ACROSS %d SEGMENTS ---\n', num_total_segments);
fprintf('Average Damping (b)  : %.4f N*m*s/rad\n', mean(b_est_all));
fprintf('Average Stiffness (k): %.4f N*m/rad\n', mean(k_est_all));
fprintf('Average TF Fit       : %.2f%%\n', mean(fit_tf_all));
fprintf('Average SS Fit       : %.2f%%\n', mean(fit_ss_all));

(* clear;
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
    "Position", double([x, y, z_height]), ...
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

%% Preallocate trajectory & steering angle storage
waypoints = zeros(1000, 3, "double");
deltas = zeros(1000, 1, "double");  % Logging vector for delta steering values

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

    %% Store x, y, z and delta values
    cnt = cnt + 1;

    % Dynamically expand preallocated memory if buffer limit is reached
    if cnt > size(waypoints, 1)
        waypoints = [waypoints; zeros(1000, 3, "double")];
        deltas = [deltas; zeros(1000, 1, "double")];
    end

    waypoints(cnt, :) = double([x, y, z_height]);
    deltas(cnt, 1) = delta; % Save logged steering angle

    %% Update the car actor in real time
    egoCar.Position = double([x, y, z_height]);

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

%% Trim preallocated arrays and package into timeseries
raw_waypoints = double(waypoints(1:cnt, :));
raw_deltas = double(deltas(1:cnt, 1));

num_points = size(raw_waypoints, 1);
t = (0:num_points-1)' * time_step;

% Export objects for Simulink 'From Workspace' blocks
waypoints_ts = timeseries(raw_waypoints, t);
deltas_ts = timeseries(raw_deltas, t);

fprintf("\nReal-time visualization stopped.\n");
fprintf("Recorded %d trajectory & delta points.\n", cnt);

%% Replay/Continue Execution with Saved Trajectory in Scenario
if cnt > 1
    fprintf("Assigning saved trajectory to vehicle scenario...\n");
    
    % Re-assign waypoints directly to egoCar for smooth scenario replay
    trajectory(egoCar, raw_waypoints, u);
    
    % Restart driving scenario simulation
    restart(scenario);
    
    fprintf("Replaying recorded trajectory in Scenario...\n");
    while advance(scenario)
        if isvalid(scenarioFigure)
            drawnow limitrate;
        else
            break;
        end
    end
    fprintf("Playback complete.\n");
else
    warning("No valid waypoints were recorded.");
end *)
clear;
clc;
close all;

%% Simulink Model Settings
modelName = 'SOFSOF';

% Open the Simulink model in memory if it isn't already open
if ~bdIsLoaded(modelName)
    fprintf("Loading Simulink model '%s'...\n", modelName);
    open_system(modelName);
end

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
    "Position", double([x, y, z_height]), ...
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

%% Preallocate trajectory, heading & steering angle storage
waypoints = zeros(1000, 3, "double");
deltas    = zeros(1000, 1, "double");  % Logging vector for delta steering values
yaws      = zeros(1000, 1, "double");  % Logging vector for heading yaw values

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

    %% Store x, y, z, delta, and yaw values
    cnt = cnt + 1;

    % Dynamically expand preallocated memory if buffer limit is reached
    if cnt > size(waypoints, 1)
        waypoints = [waypoints; zeros(1000, 3, "double")];
        deltas    = [deltas; zeros(1000, 1, "double")];
        yaws      = [yaws; zeros(1000, 1, "double")];
    end

    waypoints(cnt, :) = double([x, y, z_height]);
    deltas(cnt, 1)    = delta;
    yaws(cnt, 1)      = rad2deg(thetaCommand); % Yaw angle in degrees for Simulink 3D

    %% Update the car actor in real time
    egoCar.Position = double([x, y, z_height]);

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

%% Trim preallocated arrays and package into timeseries
raw_waypoints = double(waypoints(1:cnt, :));
raw_deltas    = double(deltas(1:cnt, 1));
raw_yaws      = double(yaws(1:cnt, 1));

num_points = size(raw_waypoints, 1);
t = (0:num_points-1)' * time_step;

% Format timeseries objects for Simulink 'From Workspace' blocks
waypoints_ts = timeseries(raw_waypoints, t);
deltas_ts    = timeseries(raw_deltas, t);

% Translation input [X, Y, Z]
pos_ts = waypoints_ts; 

% Orientation input [Roll, Pitch, Yaw] in degrees
orient_matrix = [zeros(num_points, 2), raw_yaws];
orient_ts = timeseries(orient_matrix, t);

% Assign variables directly to base workspace for Simulink access
assignin('base', 'pos_ts', pos_ts);
assignin('base', 'orient_ts', orient_ts);
assignin('base', 'deltas_ts', deltas_ts);

fprintf("\nReal-time visualization stopped.\n");
fprintf("Recorded %d trajectory points.\n", cnt);

%% Run the Simulink Model
if cnt > 1
    fprintf("Executing Simulink model '%s' with generated trajectory...\n", modelName);
    
    % Set simulation stop time to match recorded data duration
    simStopTime = sprintf('%.2f', t(end));
    set_param(modelName, 'StopTime', simStopTime);
    
    % Run Simulink Model
    sim(modelName);
    
    fprintf("Simulink simulation completed successfully.\n");
else
    warning("No valid waypoints were recorded. Simulink model execution skipped.");
end
