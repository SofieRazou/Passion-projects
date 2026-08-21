function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc)
%#codegen

    % Persistent variables to track memory smoothly across steps
    persistent k_prev b_prev initialized
    
    % Configuration Parameters
    J = 0.0103;                % Device rotational inertia (kg*m^2)
    
    % Initialization on the first step (all start at zero)
    if isempty(initialized)
        k_prev = 0.0;
        b_prev = 0.0;
        initialized = true;
    end
    
    % Default outputs initialize/fallback to previous safe state or zero
    k_theta_est = k_prev;
    b_theta_est = b_prev;
    
    % Active engagement check: Ensure sufficient motion and non-zero angle/velocity
    if abs(omega) > 0.005 && abs(theta) > 0.001
        
        % Net resistive torque absorbed by the environment
        net_torque = tau_h - J * alpha_acc;
        
        % Power-weighted distribution components using direct angle theta
        term_k = theta^2;
        term_b = omega^2;
        total_term = term_k + term_b;
        
        if total_term > 1e-5
            % Allocate torque share based on physical state magnitude safely
            torque_k = net_torque * (term_k / total_term);
            torque_b = net_torque * (term_b / total_term);
            
            % Raw calculations with safeguards against division by zero
            k_raw = abs(torque_k / (theta + sign(theta) * 1e-6));
            b_raw = abs(torque_b / (omega + sign(omega) * 1e-6));
            
            % Gentle low-pass filter to eliminate chattering and jumps
            alpha_filter = 0.05; 
            
            k_prev = (1 - alpha_filter) * k_prev + alpha_filter * k_raw;
            b_prev = (1 - alpha_filter) * b_prev + alpha_filter * b_raw;
        end
        
        % Strict physical bounding to guarantee no explosions or NaNs
        k_theta_est = min(max(0, k_prev), 50000);
        b_theta_est = min(max(0, b_prev), 200);
        
        k_prev = k_theta_est;
        b_prev = b_theta_est;
        
    else
        % When motion or angle is near zero, smoothly decay back to zero gracefully
        decay_rate = 0.1;
        k_prev = k_prev * (1 - decay_rate);
        b_prev = b_prev * (1 - decay_rate);
        
        k_theta_est = k_prev;
        b_theta_est = b_prev;
    end
    
    % Final NaN/Inf safety catch
    if ~isfinite(k_theta_est), k_theta_est = 0; end
    if ~isfinite(b_theta_est), b_theta_est = 0; end
end
