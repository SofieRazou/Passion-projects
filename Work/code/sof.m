filename = 'yaw_shared.bin';

m = memmapfile(filename,...
    'Format','double',...
    'Writable',false);

yaw = m.Data;
yaw_value = yaw(1);
