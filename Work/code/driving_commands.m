clear;
clc;

%% Vehicle parameters
u = 30;             % Vehicle speed [m/s]
x_0 = 0.0;          % Initial x-position [m]
y_0 = 0.0;          % Initial y-position [m]
theta_0 = 0.0;      % Initial vehicle heading [rad]
L = 1.0;            % Wheelbase [m]
time_step = 0.001;  % Simulation timestep [s]

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
duration = 30;       % Simulation duration [s]
startTime = tic;
cnt = 0;

while toc(startTime) < duration

    %% Read a complete sample from shared memory
    validSample = false;

    while ~validSample
        sequenceBefore = sharedMemory.Data.Sequence;

        % An odd sequence means Python is currently writing
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

    %% Convert commands to a numeric row vector
    commands = double(newCommands(:).');

    if numel(commands) ~= 2
        error( ...
            "Expected two commands, but received %d.", ...
            numel(commands));
    end

    %% Extract steering command and heading command
    delta = commands(1);
    thetaCommand = commands(2);

    %% Run one vehicle-model step
    [xNew, yNew, thetaNew] = run_driving_venv( ...
        delta, ...
        thetaCommand, ...
        u, ...
        L, ...
        x_0, ...
        y_0, ...
        theta_0, ...
        time_step);

    %% Append the new vehicle state
    cnt = cnt + 1;

    trajectory(cnt, :) = [ ...
        xNew, ...
        yNew, ...
        thetaNew ...
    ];

    %% Update states for the next simulation step
    x_0 = xNew;
    y_0 = yNew;
    theta_0 = thetaNew;

    pause(time_step);
end

%% Export the generated trajectory
outputScenario = exportToDrivingScenario(trajectory);
