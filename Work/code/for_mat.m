filePath = "C:\Temp\shared_data.bin";

sharedMemory = memmapfile( ...
    filePath, ...
    "Writable", false, ...
    "Format", { ...
        "uint64", [1 1], "Sequence"; ...
        "double", [1 2], "Values" ...
    });

while true
    % Read until a complete, consistent sample is available
    while true
        sequenceBefore = sharedMemory.Data.Sequence;

        % An odd sequence means Python is writing
        if mod(sequenceBefore, 2) ~= 0
            continue;
        end

        values = sharedMemory.Data.Values;
        sequenceAfter = sharedMemory.Data.Sequence;

        % Ensure Python did not update the values during reading
        if sequenceBefore == sequenceAfter && ...
                mod(sequenceAfter, 2) == 0
            break;
        end
    end

    x = values(1);
    y = values(2);

    fprintf("x = %.4f, y = %.4f\n", x, y);

    pause(0.01);
end


%% Remove unused rows
trajectory = trajectory(1:cnt, :);

%% Display the collected trajectory
figure;
plot(trajectory(:, 1), trajectory(:, 2));
xlabel("x [m]");
ylabel("y [m]");
title("Vehicle trajectory");
grid on;
axis equal;
