clear;
clc;

%% Vehicle and simulation settings
time_step = 0.01;   % Sampling period [s]
duration = 30;      % Total simulation duration [s]

u = 30;             % Vehicle velocity [m/s]
L = 1.0;            % Vehicle wheelbase [m]

x = 0.0;            % Initial x-position [m]
y = 0.0;            % Initial y-position [m]

%% Shared-memory file
filePath = "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

if ~isfile(filePath)
    error("Shared-memory file not found: %s", filePath);
end

%% Memory layout
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

%% Preallocate trajectory
maxSamples = ceil(duration / time_step);
trajectory = zeros(maxSamples, 2);

cnt = 0;
startTime = tic;

while toc(startTime) < duration

    %% Read one complete sample
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

        % Accept only a complete, unchanged sample
        validSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;
    end

    %% Convert values to a 1-by-2 numeric vector
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected 2 values from shared_data.bin, received %d.", ...
            numel(commands));
    end

    %% Extract commands
    delta = commands(1);
    thetaCommand = commands(2);

    %% Run one vehicle simulation step
    [xNew, yNew] = run_driving_venv( ...
        delta, ...
        thetaCommand, ...
        u, ...
        L, ...
        x, ...
        y, ...
        time_step);

    %% Update vehicle position
    x = xNew;
    y = yNew;

    %% Store trajectory
    cnt = cnt + 1;

    if cnt > size(trajectory, 1)
        trajectory = [trajectory; zeros(1000, 2)];
    end

    trajectory(cnt, :) = [x, y];

    %% Display current values
    fprintf( ...
        "delta = %.4f, theta = %.4f, x = %.4f, y = %.4f\n", ...
        delta, thetaCommand, x, y);

    pause(time_step);
end

%% Remove unused trajectory rows
trajectory = trajectory(1:cnt, :);

%% Plot vehicle trajectory
figure;
plot(trajectory(:, 1), trajectory(:, 2), "LineWidth", 1.5);

xlabel("x [m]");
ylabel("y [m]");
title("Vehicle trajectory");

grid on;
axis equal;
