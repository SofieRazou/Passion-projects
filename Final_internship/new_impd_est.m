function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc, dt)
%#codegen

    % Persistent variables for estimator state persistence across simulation steps
    persistent theta_est P initialized
    
    % Initialization on the first step
    if isempty(initialized)
        theta_est = [5000; 10]; % Initial parameter guesses [k_theta; b_theta]
        P = 100 * eye(2);       % Lower initial covariance to prevent aggressive initial spikes
        initialized = true;
    end
    
    % Configuration Parameters
    theta_wall = 0.0;          % Virtual wall boundary angle (rad)
    J = 0.0103;                  % Device rotational inertia (kg*m^2)
    
    theta_err = theta - theta_wall;
    
    % 1. Strict Deadzone: Only update inside the wall and away from zero-crossing noise
    % Also require minimum velocity to ensure the power equation has sufficient excitation
    if theta_err < -0.002 && abs(omega) > 0.05
        
        % Regressor vector phi = [theta_err * omega; omega^2]
        phi = [theta_err * omega; omega^2];
        
        % Output measurement y = Input Power - Kinetic Power Change
        y = tau_h * omega - J * omega * alpha_acc;
        
        % 2. Normalized Least Squares Adaptation (Significantly more stable than raw RLS)
        % Adding a small leakage/regularization factor (epsilon) to prevent division by zero
        epsilon = 1e-3;
        phi_norm_sq = phi' * phi;
        
        if phi_norm_sq > 1e-4
            % Normalized error formulation
            prediction_error = y - phi' * theta_est;
            
            % Adaptation gain with leakage factor to keep estimates bounded
            gamma = 0.05; % Adaptation rate (tuning knob for speed vs stability)
            
            % Update parameter vector smoothly
            theta_est = theta_est + (gamma / (epsilon + phi_norm_sq)) * phi * prediction_error;
        end
    end
    
    % 3. Hard Physical Clamping / Projections
    % Keeps estimates inside realistic human-haptic bounds (preventing runaway numbers)
    k_theta_est = min(max(0, theta_est(1)), 50000); % Cap stiffness at 50 kNm/rad
    b_theta_est = min(max(0, theta_est(2)), 200);   % Cap damping at 200 Nms/rad
end
