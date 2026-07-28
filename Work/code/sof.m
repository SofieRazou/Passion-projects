function yaw = read_yaw()

persistent m

% Default output
yaw = 0;

if isempty(m)
    filename = 'yaw_shared.bin';

    % Check that the file exists
    if ~isfile(filename)
        warning('Shared memory file "%s" not found.', filename);
        return;
    end

    try
        m = memmapfile(filename, ...
            'Format', 'double', ...
            'Writable', false);
    catch ME
        warning('Failed to open memory-mapped file:\n%s', ME.message);
        return;
    end
end

% Read the yaw value
yaw = m.Data(1);

end
