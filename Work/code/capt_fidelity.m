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

% Configure UDP settings to match your dSPACE Python sender
localIP = "127.0.0.1";
localPort = 50000;

% Create the UDP port object for IPv4
u = udpport("IPV4", "LocalHost", localIP, "LocalPort", localPort);

disp('========================================================');
disp(' Listening for dSPACE UDP data stream on port 50000...  ');
disp(' Press Ctrl+C in the command window to stop.            ');
disp('========================================================');

% Initialize data storage arrays for live plotting
time_data = [];
angle_data = [];
torque_data = [];

% Set up a live figure window
fig = figure('Name', 'dSPACE Live UDP Data Receiver', 'Position', [100, 100, 800, 500]);

try
    while true
        % Check if a UDP packet has arrived
        if u.NumBytesAvailable > 0
            % Read the incoming UDP packet string
            rawString = readline(u);
            
            % Decode the JSON string into a MATLAB struct
            dataPacket = jsondecode(rawString);
            
            % Extract fields
            t_elapsed = dataPacket.elapsed_time;
            
            % Extract angle (Out1) and torque safely
            if isfield(dataPacket, 'Out1') && ~isempty(dataPacket.Out1)
                angle_val = dataPacket.Out1;
            else
                angle_val = NaN;
            end
            
            if isfield(dataPacket, 'Torque') && ~isempty(dataPacket.Torque)
                torque_val = dataPacket.Torque;
            else
                torque_val = NaN;
            end
            
            % Append data to arrays
            time_data(end+1, 1) = t_elapsed;
            angle_data(end+1, 1) = angle_val;
            torque_data(end+1, 1) = torque_val;
            
            % Print packet data to command window optionally
            fprintf('Time: %.2fs | Angle (Out1): %.4f | Torque: %.4f\n', ...
                t_elapsed, angle_val, torque_val);
            
            % Update live plots dynamically
            if length(time_data) > 1
                subplot(2,1,1);
                plot(time_data, angle_data, 'b-', 'LineWidth', 1.2);
                grid on;
                ylabel('Angle / Out1');
                title('Live dSPACE Data Stream via UDP');
                
                subplot(2,1,2);
                plot(time_data, torque_data, 'r-', 'LineWidth', 1.2);
                grid on;
                xlabel('Elapsed Time [s]');
                ylabel('Torque [Nm]');
                
                drawnow limitrate;
            end
        end
    end

catch ME
    % Catch loop interruption (e.g., Ctrl+C)
    disp('Receiver stopped by user.');
    disp(ME.message);
end

% Clean up and close the UDP port properly
clear u;
disp('UDP receiver socket closed successfully.');
