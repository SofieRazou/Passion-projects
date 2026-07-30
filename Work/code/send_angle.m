function angle = read_angle_from_file()
    % Declare MATLAB functions as extrinsic so C-code generator ignores file I/O
    coder.extrinsic('fopen', 'fclose', 'fgetl', 'exist', 'str2double');

    % Define file name
    filename = 'latest_angle.txt';

    % Persistent variable holds the previous valid angle across simulation steps
    persistent last_angle;
    if isempty(last_angle)
        last_angle = 0.0; % Initial fallback angle
    end

    current_angle = last_angle;

    % Check if file exists
    if exist(filename, 'file') == 2
        try
            fileID = fopen(filename, 'r');
            if fileID ~= -1
                angle_str = fgetl(fileID);
                fclose(fileID);
                
                % Process text line
                if ischar(angle_str) && ~isempty(angle_str)
                    parsed_val = str2double(angle_str);
                    if ~isnan(parsed_val)
                        current_angle = parsed_val;
                        last_angle = current_angle; % Update stored state
                    end
                end
            end
        catch
            % If file access conflicts occur during a step, keep the last read angle
            current_angle = last_angle;
        end
    end

    % Output signal to Simulink
    angle = double(current_angle);
end
