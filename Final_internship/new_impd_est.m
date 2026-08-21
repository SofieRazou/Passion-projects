function a = fcn(Eobs, omega)

persistent a_prev

%% Parameters
gamma = 0.05;          % adaptation gain (tune 0.01-0.2)
omega_min = 1e-3;      % avoid division by zero

a_min = 0.05;          % minimum damping
a_max = 5.0;           % maximum damping

%% Initialization
if isempty(a_prev)
    a_prev = a_min;
end

%% Safe velocity
omega_safe = max(abs(omega), omega_min);

%% Adaptation

if Eobs < 0

    % Increase damping when passivity is violated
    da = -gamma * Eobs / (omega_safe^2);

    a = a_prev + da;

else

    % Slowly relax damping toward minimum
    relaxation = 0.01;

    a = a_prev - relaxation*(a_prev-a_min);

end

%% Saturation
a = min(max(a,a_min),a_max);

%% Save state
a_prev = a;

end


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
