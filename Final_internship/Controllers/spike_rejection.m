function [k_out, b_out] = fcn(k_in, b_in)
%#codegen
    persistent k_last b_last initialized
    
    if isempty(initialized)
        k_last = 0;
        b_last = 0;
        initialized = true;
    end
    
    % Spike Rejection Logic:
    % If the incoming value drops suddenly (more than 0.5 below the last valid level),
    % reject the drop and hold the previous stable value.
    if k_in < (k_last - 0.5) && k_last > 1
        k_out = k_last; % Hold the upper level, ignore the drop-spike
    else
        k_out = k_in;   % Accept normal values
        k_last = k_out; % Update last valid memory
    end
    
    if b_in < (b_last - 0.1) && b_last > 0.05
        b_out = b_last;
    else
        b_out = b_in;
        b_last = b_out;
    end
end
