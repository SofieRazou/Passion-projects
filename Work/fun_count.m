function [y, count] = fcn(u)
    % 1. Use a separate persistent variable for state tracking
    persistent p_count;
    
    % 2. Initialize persistent state on the first call
    if isempty(p_count)
        p_count = 0;
    end
    
    % 3. Execute conditional logic
    if u
        y = 1;
        p_count = p_count + 1; 
    else
        y = 0;
    end
    
    % 4. Explicitly assign the output argument on ALL execution paths
    count = p_count;
end
