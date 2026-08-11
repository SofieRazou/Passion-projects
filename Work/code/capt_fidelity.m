%% =============================================================
%        PURE STIFFNESS (k-only) TRANSFER FUNCTION & BODE
% =============================================================
J_val = 0.0103;          % Fixed motor inertia
k_avg = 42.95 + 1;           % Your average estimated stiffness
b_avg = 9.1079;
% Define Transfer Function with b = 0
num = [1];
den = [J_val, b_avg, k_avg]; % Notice the 0 for the damping coefficient term
sys_k_only = tf(num, den);

disp('--- PURE STIFFNESS TRANSFER FUNCTION (b=0) ---');
disp(sys_k_only);

% Plot Bode Diagram
figure('Name', 'k-Only System Bode Diagram');
bode(sys_k_only);
grid on;
title(sprintf('Bode Plot (k = %.2f, b = %.2f)', k_avg, b_avg));


clear
close all
clc

% Clear any lingering port allocations from previous runs
clear u;

% R2020b Compatible udpport setup
% We specify the local port explicitly using name-value pairs
localPort = 50000;
u = udpport("byte", "LocalPort", localPort);

disp('========================================================');
disp(' udpport connected successfully on port 50000 (R2020b)  ');
disp(' Press Ctrl+C in the command window to stop.            ');
disp('========================================================');

time_data = [];
angle_data = [];
torque_data = [];

figure('Name', 'Live dSPACE UDP Stream (R2020b)', 'Position', [100, 100, 800, 500]);

try
    while true
        % Check if bytes are available in the buffer
        if u.NumBytesAvailable > 0
            % Read string line using built-in readline for byte-type udpport
            rawString = readline(u);
            
            if ~isempty(rawString)
                % Decode JSON packet coming from Python
                dataPacket = jsondecode(rawString);
                
                t_elapsed = dataPacket.elapsed_time;
                angle_val = dataPacket.Out1;
                torque_val = dataPacket.Torque;
                
                % Store data for plots
                time_data(end+1, 1) = t_elapsed;
                angle_data(end+1, 1) = angle_val;
                torque_data(end+1, 1) = torque_val;
                
                fprintf('Time: %.2fs | Angle: %.4f | Torque: %.4f\n', t_elapsed, angle_val, torque_val);
                
                % Live plot update
                if length(time_data) > 1
                    subplot(2,1,1);
                    plot(time_data, angle_data, 'b-', 'LineWidth', 1.2);
                    grid on;
                    ylabel('Angle / Out1');
                    title('Live dSPACE Data Stream (R2020b)');
                    
                    subplot(2,1,2);
                    plot(time_data, torque_data, 'r-', 'LineWidth', 1.2);
                    grid on;
                    xlabel('Elapsed Time [s]');
                    ylabel('Torque [Nm]');
                    
                    drawnow limitrate;
                end
            end
        end
    end

catch ME
    disp('Receiver stopped by user.');
    disp(ME.message);
end

% Clean up port object
clear u;
disp('udpport closed.');
