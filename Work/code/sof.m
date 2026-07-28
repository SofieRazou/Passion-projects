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


import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

destinations = [
    ("127.0.0.1", 5005),
    ("127.0.0.1", 5006)
]

while True:
    yaw = 1.234
    data = f"{yaw:.6f}".encode()

    for dest in destinations:
        sock.sendto(data, dest)

end
