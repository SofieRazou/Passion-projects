function kappa = fcn(tau_raw, theta)
%#codegen
    persistent sum_tau_theta sum_theta_sq
    
    % Define a zero offset (adjust this based on your load cell tare)
    zero_offset = 0.0; 
    tau_actual = tau_raw - zero_offset;
    
    % Initialize persistent memory on the first step
    if isempty(sum_tau_theta)
        sum_tau_theta = 0;
        sum_theta_sq = 0;
    end
    
    % Accumulate values at every simulation step
    sum_tau_theta = sum_tau_theta + (tau_actual * theta);
    sum_theta_sq = sum_theta_sq + (theta^2);
    
    % Prevent division by zero
    if sum_theta_sq > 1e-6
        kappa = sum_tau_theta / sum_theta_sq;
    else
        kappa = 0;
    end
end
