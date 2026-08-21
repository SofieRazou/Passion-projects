function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc)
%#codegen

    % Persistent variables to remember and smooth estimates over time
    persistent k_prev b_prev initialized
    
    % Configuration Parameters
    theta_wall = 0.0;          % Virtual wall boundary angle (rad)
    J = 0.0103;                % Updated device rotational inertia (kg*m^2)
    
    % Initialization on the first step
    if isempty(initialized)
        k_prev = 0;
        b_prev = 0;
        initialized = true;
    end
    
    theta_err = theta - theta_wall;
    
    % Default outputs (hold previous values or zero if outside wall)
    k_theta_est = k_prev;
    b_theta_est = b_prev;
    
    % Only compute when actively inside the wall and moving with sufficient velocity
    if theta_err < -0.001 && abs(omega) > 0.01
        
        % Net resistive torque absorbed by the environment
        net_torque = tau_h - J * alpha_acc;
        
        % Instantaneous power split based on energy distribution proportions 
        % (weighted by the squared contribution of each state)
        term_k = theta_err^2;
        term_b = omega^2;
        total_term = term_k + term_b;
        
        if total_term > 1e-6
            % Dynamically allocate torque share based on physical state magnitude
            torque_k = net_torque * (term_k / total_term);
            torque_b = net_torque * (term_b / total_term);
            
            % Raw calculations avoiding division singularities
            k_raw = abs(torque_k / theta_err);
            b_raw = abs(torque_b / omega);
            
            % Smoothing factor (alpha) for low-pass filter (0.05 = smooth, 0.5 = fast)
            alpha_filter = 0.1;
            
            % Update estimates with memory smoothing
            k_prev = (1 - alpha_filter) * k_prev + alpha_filter * k_raw;
            b_prev = (1 - alpha_filter) * b_prev + alpha_filter * b_raw;
        end
        
        % Bounded physical filtering to prevent jumps, NaN, or explosions
        k_theta_est = min(max(0, k_prev), 50000);
        b_theta_est = min(max(0, b_prev), 200);
        
        % Update persistent states
        k_prev = k_theta_est;
        b_prev = b_theta_est;
        
    else
        % If outside the wall, smoothly decay or hold values
        k_theta_est = k_prev;
        b_theta_est = b_prev;
    end
end
