clear;
clc;

%% Settings
time_step = 0.01;   % Python writes approximately every 0.01 s
duration = 30;      % Run time [s]

%% Shared-memory file
filePath = "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

if ~isfile(filePath)
    error("Shared-memory file not found: %s", filePath);
end

%% Memory layout:
% Bytes 1-8:   uint64 sequence
% Bytes 9-16:  double command 1
% Bytes 17-24: double command 2

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

        % Accept only if Python did not write during the read
        validSample = ...
            sequenceBefore == sequenceAfter && ...
            mod(sequenceAfter, 2) == 0;
    end

    %% Convert to a normal 1-by-2 MATLAB vector
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected 2 values from shared_data.bin, received %d.", ...
            numel(commands));
    end

    %% Read commands
    delta = commands(1);
    thetaCommand = commands(2);

    %% Send commands to the driving environment
    [xNew, yNew] = run_driving_venv(delta, thetaCommand);

    %% Store returned position
    cnt = cnt + 1;

    if cnt > size(trajectory, 1)
        trajectory = [trajectory; zeros(1000, 2)];
    end

    trajectory(cnt, :) = [xNew, yNew];

    %% Optional monitoring
    fprintf( ...
        "delta = %.4f, theta = %.4f, x = %.4f, y = %.4f\n", ...
        delta, thetaCommand, xNew, yNew);

    pause(time_step);
end

%% Remove unused rows
trajectory = trajectory(1:cnt, :);

%% Plot trajectory
figure;
plot(trajectory(:, 1), trajectory(:, 2), "LineWidth", 1.5);
xlabel("x [m]");
ylabel("y [m]");
title("Vehicle trajectory");
grid on;
axis equal;
