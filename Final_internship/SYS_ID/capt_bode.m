% =============================================================
% 2. CONFIGURE UDP RECEIVER
% =============================================================
localPort = 50000;
udpRx = dsp.UDPReceiver('LocalIPPort', localPort, ...
    'MaximumMessageLength', 1024, ...
    'MessageDataType', 'uint8');
setup(udpRx);

disp('========================================================');
disp(' Listening for dSPACE UDP data stream on port 50000... ');
disp(' (Will automatically stop & plot after 2s of silence) ');
disp('========================================================');

time_data = [];
angle_data = [];
torque_data = [];
fig = figure('Name', 'Live dSPACE Data Receiver', 'Position', [100, 100, 800, 500]);

% Timeout parameters
inactivityTimeout = 2.0; % Seconds to wait before stopping
tic; % Start the inactivity timer

while true
    % Receive raw bytes using the actual udpRx object
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
            figure(fig);
            
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
            disp('--- UDP stream inactivity timeout reached. Processing System ID & Bode Plot... ---');
            break;
        end
    end
end

% Release the UDP receiver object
release(udpRx);

%% Post-Processing: System Identification & Bode Plot Generation
if length(time_data) > 10
    % Calculate uniform sample time step
    dt = mean(diff(time_data));
    
    % Create iddata object: Input = Torque, Output = Angle
    dataObj = iddata(angle_data, torque_data, dt);
    dataObj.InputName = 'Torque';
    dataObj.OutputName = 'Angle';
    
    % Fit a 2nd-order Mass-Spring-Damper Transfer Function model
    opt = tfestOptions;
    opt.Display = 'on';
    
    sys_identified = tfest(dataObj, 2, 0, opt);
    
    disp('--- Identified System Transfer Function ---');
    disp(sys_identified);
    
    % Plot the Bode Diagram of the empirical/identified system
    figure('Name', 'Bode Plot of Empirical System');
    bode(sys_identified);
    grid on;
    title('Bode Plot of Empirical dSPACE System (Identified Model)');
else
    disp('Not enough data collected to perform system identification.');
end
