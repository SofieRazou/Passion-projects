clear;
clc;

%% Vehicle parameters
u = 30;             % Vehicle speed [m/s]
x_0 = 0.0;          % Initial x-position [m]
y_0 = 0.0;          % Initial y-position [m]
L = 1.0;            % Wheelbase [m]
time_step = 0.001;  % Simulation step [s]

trajectory = [];
commands = [0.0, 0.0];

%% Shared-memory file
filePath = "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

sharedMemory = memmapfile( ...
    filePath, ...
    "Writable", false, ...
    "Format", { ...
        "uint64", [1 1], "Sequence"; ...
        "double", [1 2], "Values" ...
    });

%% Simulation settings
duration = 30;       % Run for 30 seconds
startTime = tic;
cnt = 0;

while toc(startTime) < duration

    %% Read one complete shared-memory sample
    validSample = false;

    while ~validSample
        sequenceBefore = sharedMemory.Data.Sequence;

        % Odd sequence means Python is currently writing
        if mod(sequenceBefore, 2) ~= 0
            pause(0.0001);
            continue;
        end

        newCommands = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        validSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;
    end

    commands = double(newCommands);

    %% Extract commands
    delta = commands(1);
    theta = commands(2);

    %% Run one simulation step
    newTrajectoryPoint = run_driving_venv( ...
        delta, theta, u, L, x_0, y_0, time_step);

    %% Append the new point
    trajectory(end + 1, :) = newTrajectoryPoint;

    %% Update the initial state for the next iteration
    % Adjust these indices to match run_driving_venv's output format.
    x_0 = newTrajectoryPoint(1);
    y_0 = newTrajectoryPoint(2);

    cnt = cnt + 1;

    %% Maintain approximately the requested time step
    pause(time_step);
end

%% Export completed trajectory
outputScenario = exportToDrivingScenario(trajectory);
