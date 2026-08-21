function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc)
%#codegen

    % Configuration Parameters
    theta_wall = 0.0;          % Virtual wall boundary angle (rad)
    J = 0.0103;                % Updated device rotational inertia (kg*m^2)
    
    theta_err = theta - theta_wall;
    
    % Default values (fallback if outside the wall)
    k_theta_est = 0;
    b_theta_est = 0;
    
    % Only compute when actively inside the wall and moving with sufficient velocity
    if theta_err < -0.001 && abs(omega) > 0.01
        
        % Net resistive torque absorbed by the environment
        net_resistive_torque = tau_h - J * alpha_acc;
        
        % Direct algebraic estimation splitting the load between stiffness and damping
        if abs(theta_err) > 1e-4
            k_raw = abs((net_resistive_torque * 0.7) / theta_err); 
        else
            k_raw = 0;
        end
        
        if abs(omega) > 1e-4
            b_raw = abs((net_resistive_torque * 0.3) / omega);
        else
            b_raw = 0;
        end
        
        % Bounded physical filtering to prevent jumps or NaN
        k_theta_est = min(max(0, k_raw), 50000);
        b_theta_est = min(max(0, b_raw), 200);
        
    end
end
