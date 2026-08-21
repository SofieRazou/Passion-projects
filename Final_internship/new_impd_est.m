function a = fcn(E_generated, sum_omega2_dt, cycle_completed)
%#codegen
% Adaptive Damping Regulation based on Dinc et al., 2024
% E_generated: The energy leaked/generated during the last cycle (Joules).
% sum_omega2_dt: The integral of omega^2 * dt over the cycle.
% cycle_completed: Boolean flag (1 if a cycle just ended, 0 otherwise).

    persistent a_prev
    
    %% Parameters
    a_min = 0.05;          % minimum damping transparency limit (Nms/rad)
    a_max = 5.0;           % maximum damping stability limit (Nms/rad)
    epsilon = 1e-5;        % safe minimum to avoid division by zero
    
    %% Initialization
    if isempty(a_prev)
        a_prev = a_min;
    end
    
    %% Cycle-Based Adaptation Logic
    % We only update the damping value at the exact completion of a cycle
    % to prevent high-frequency chattering and noise.
    
    if cycle_completed == 1
        
        % If E_generated > 0, the virtual environment leaked energy (passivity violated).
        if E_generated > 0 
            
            % The exact required damping to dissipate the generated energy
            safe_denominator = max(sum_omega2_dt, epsilon);
            da = E_generated / safe_denominator; 
            
            a = a_prev + da;
            
        else
            % If no energy was generated (system is dissipative/stable), 
            % slowly relax damping toward minimum for high transparency.
            relaxation = 0.1; % Tune how fast it returns to transparent state
            a = a_prev - relaxation * (a_prev - a_min);
        end
        
        %% Saturation bounds
        a = min(max(a, a_min), a_max);
        
        %% Save state for the next cycle
        a_prev = a;
        
    else
        % If in the middle of a cycle, hold the previous damping value
        a = a_prev;
    end

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
