u = 30; %m/s
x_0 = 0.0; %m
y_0 = 0.0; %m
L = 1; %m
time_step = 0.001;
trajectory = {};
commands = {};

filePath = "C:\Users\javot\Desktop\sofia_code\shared_data.bin";

sharedMemory = memmapfile( ...
    filePath, ...
    "Writable", false, ...
    "Format", { ...
        "uint64", [1 1], "Sequence"; ...
        "double", [1 2], "Values" ...
    });

while true
    % Read until a complete sample
    while true
        sequenceBefore = sharedMemory.Data.Sequence;

        % odd sequence means Python is writing
        if mod(sequenceBefore, 2) ~= 0
            continue;
        end

        commands = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        if sequenceBefore == sequenceAfter && ...
                mod(sequenceAfter, 2) == 0
            break;
        end
    end

    x = commands(1);
    y = commands(2);

    pause(0.01);
end

cnt = 0;
while isempty(commands)
    
    trajectory{cnt+1}(end+1) = run_driving_venv(delta, theta, u, L, x_0, y_0, time_step);
    cnt = cnt + 1;
    
end
outputScenario = exportToDrivingScenario(trajectory);
