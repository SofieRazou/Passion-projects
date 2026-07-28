function yaw = read_yaw()

persistent m

if isempty(m)
    filename = 'yaw_shared.bin';

    m = memmapfile(filename, ...
        'Format', 'double', ...
        'Writable', false);
end

yaw = m.Data(1);

end
