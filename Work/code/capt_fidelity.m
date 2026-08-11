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

% =============================================================
% 1. PURE STIFFNESS (k-only) THEORETICAL TRANSFER FUNCTION & BODE
% =============================================================
J_val = 0.0103;            % Fixed motor inertia
k_avg = 42.95 + 1;         % Average estimated stiffness
b_avg = 9.1079;

num = [1];
den = [J_val, b_avg, k_avg]; 
sys_k_only = tf(num, den);

disp('--- PURE STIFFNESS TRANSFER FUNCTION (b=0) ---');
disp(sys_k_only);

% Plot Theoretical Bode Diagram
figure('Name', 'k-Only System Bode Diagram');
bode(sys_k_only);
grid on;
title(sprintf('Theoretical Bode Plot (k = %.2f, b = %.2f)', k_avg, b_avg));


% =============================================================
% 2. CONFIGURE UDP RECEIVER
% =============================================================
localPort = 50000;
udpRx = dsp.UDPReceiver('LocalIPPort', localPort, ...
                        'MaximumMessageLength', 1024, ...
                        'MessageDataType', 'uint8');
setup(udpRx);

disp('========================================================');
disp(' Listening for dSPACE UDP data stream on port 50000...  ');
disp(' (Will automatically stop & plot after 2s of silence)   ');
disp('========================================================');

time_data = [];
angle_data = [];
torque_data = [];

fig = figure('Name', 'Live dSPACE Data Receiver', 'Position', [100, 100, 800, 500]);

% Timeout parameters
inactivityTimeout = 2.0; % Seconds to wait before stopping automatically
tic;                    % Start inactivity timer

try
    while true
        rawBytes = udpRx();
        
        if ~isempty(rawBytes)
            % Reset inactivity timer since a packet just arrived
            tic; 
            
            rawString = char(rawBytes');
            dataPacket = jsondecode(rawString);
            
            t_elapsed = dataPacket.elapsed_time;
            angle_val = dataPacket.Out1;
            torque_val = dataPacket.Torque;
            
            time_data(end+1, 1) = t_elapsed;
            angle_data(end+1, 1) = angle_val;
            torque_data(end+1, 1) = torque_val;
            
            fprintf('Time: %.2fs | Angle: %.4f | Torque: %.4f\n', t_elapsed, angle_val, torque_val);
            
            if length(time_data) > 1
                subplot(2,1,1);
                plot(time_data, angle_data, 'b-', 'LineWidth', 1.2);
                grid on;
                ylabel('Angle / Out1');
                title('Live dSPACE Data Stream');
                
                subplot(2,1,2);
                plot(time_data, torque_data, 'r-', 'LineWidth', 1.2);
                grid on;
                xlabel('Elapsed Time [s]');
                ylabel('Torque [Nm]');
                
                drawnow limitrate;
            end
        else
            % Check if we've exceeded the inactivity timeout window
            if toc > inactivityTimeout
                disp('--- UDP stream inactivity timeout reached. Processing Bode plot... ---');
                break;
            end
        end
    end

catch ME
    disp(['Receiver stopped: ', ME.message]);
end

% Release the UDP resource
release(udpRx);
disp('UDP receiver closed.');


% =============================================================
% 3. EMPIRICAL MODEL & BODE PLOT (Post-processing Recorded Data)
% =============================================================
if length(time_data) > 10
    % Calculate uniform sample time
    Ts = mean(diff(time_data));
    
    % Create an iddata object (Input: Torque, Output: Angle/Out1)
    data = iddata(angle_data, torque_data, Ts);
    
    % Estimate transfer function model from recorded stream
    sys_empirical = tfest(data, 2, 1);
    
    % Generate the Empirical Bode Plot in a new figure window
    
    figure('Name', 'System Identification - Empirical Bode Plot', 'Position', [200, 200, 700, 500]);
    bode(sys_empirical);
    grid on;
    title('Bode Plot of Empirical dSPACE System');
    disp('Empirical Bode plot generated successfully.');
else
    disp('Not enough data collected to generate a reliable empirical Bode plot.');
end
