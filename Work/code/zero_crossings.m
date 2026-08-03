function crossings = fcn(angle)

persistent prev_angle crossings_count

if isempty(prev_angle)
    prev_angle = angle;
    crossings_count = 0;
end

% Detect sign change (zero crossing)
if (angle > 0 && prev_angle < 0) || (angle < 0 && prev_angle > 0)
    crossings_count = crossings_count + 1;
end

% Update previous value
prev_angle = angle;

% Output
crossings = crossings_count;

end
