% read_angle.m
filename = 'latest_angle.txt';

disp('Listening for angle updates from Python... Press Ctrl+C to stop.');

last_angle = NaN;

while true
    if exist(filename, 'file') == 2
        try
            % Read text contents from the file
            fileID = fopen(filename, 'r');
            if fileID ~= -1
                angle_str = fgetl(fileID);
                fclose(fileID);
                
                % Convert string to double
                if ischar(angle_str) && ~isempty(angle_str)
                    current_angle = str2double(angle_str);
                    
                    % Only print/process when value actually updates
                    if ~isnan(current_angle) && current_angle ~= last_angle
                        fprintf('Current Angle: %6.2f deg\n', current_angle);
                        last_angle = current_angle;
                        
                        % Place your MATLAB/Simulink variable assignment here:
                        % assignin('base', 'angle_val', current_angle);
                    end
                end
            end
        catch
            % Ignore file locking conflicts during rapid updates
        end
    end
    
    % Small delay (e.g., 10ms = 100 Hz sampling rate)
    pause(0.01);
end
