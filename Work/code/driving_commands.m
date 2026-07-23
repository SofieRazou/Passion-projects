clear;
clc;

%% Simulation settings
time_step = 0.001;   % Sampling period [s]
duration = 30;       % Duration [s]

trajectory = zeros(ceil(duration / time_step), 2);
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

%% Run simulation
startTime = tic;
cnt = 0;

while toc(startTime) < duration

    %% Read a complete shared-memory sample
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

    %% Ensure commands is a 1-by-2 numeric vector
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected two command values, but received %d.", ...
            numel(commands));
    end

    delta = commands(1);
    thetaCommand = commands(2);

    %% Run one driving-environment update
    [xNew, yNew] = run_driving_venv(delta, thetaCommand);

    %% Store the returned position
    cnt = cnt + 1;

    if cnt > size(trajectory, 1)
        trajectory(end + 1000, 2) = 0;
    end

    trajectory(cnt, :) = [xNew, yNew];

    pause(time_step);
end

%% Remove unused preallocated rows
trajectory = trajectory(1:cnt, :);

%% Export trajectory
outputScenario = exportToDrivingScenario(trajectory);
