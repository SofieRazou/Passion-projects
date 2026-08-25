% Real-time UDP Data Acquisition & System Identification Script
% This script logs live angle and torque data via UDP, then fits 
% a mass-spring-damper model and plots its Bode response.
clear;
close all;
clc; 
time_data = [];
angle_data = [];
torque_data = [];
inactivityTimeout = 5; % seconds of silence to trigger post-processing

disp('--- Listening for UDP data stream... ---');
tic;

while true
    % Replace with your actual UDP reading function/object (e.g., read(u))
    rawBytes = getAudioOrUDPData(); 
    
    if ~isempty(rawBytes)
        tic; % Reset inactivity timer since a packet arrived
        
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
        if toc > inactivityTimeout
            disp('--- UDP stream inactivity timeout reached. Processing System ID & Bode Plot... ---');
            break;
        end
    end
end

%% Post-Processing: System Identification & Bode Plot Generation
if length(time_data) > 10
    % Ensure uniform or handled time vector for iddata
    dt = mean(diff(time_data));
    
    % Create iddata object: Input = Torque, Output = Angle (or vice versa depending on system definition)
    dataObj = iddata(angle_data, torque_data, dt);
    dataObj.InputName = 'Torque';
    dataObj.OutputName = 'Angle';
    
    % Fit a 2nd-order Mass-Spring-Damper Transfer Function (1 input, 1 output)
    % Using a grey-box or standard transfer function estimation (tfest)
    opt = tfestOptions;
    opt.Display = 'on';
    
    % Estimating a 2nd order system with 0 zeros and 2 poles (typical mass-spring-damper)
    sys_identified = tfest(dataObj, 2, 0, opt);
    
    disp('--- Identified System Transfer Function ---');
    disp(sys_identified);
    
    % Plot the Bode Diagram of the empirical/identified system
    figure;
    bode(sys_identified);
    grid on;
    title(sprintf('Bode Plot of Empirical dSPACE System (Identified Model)'));
else
    disp('Not enough data collected to perform system identification.');
end
