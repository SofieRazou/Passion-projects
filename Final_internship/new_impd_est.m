function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc, dt)
%#codegen

    % Persistent variables for RLS state persistence across simulation steps
    persistent theta_est P initialized
    
    % Initialization on the first step
    if isempty(initialized)
        theta_est = [1000; 5]; % Initial parameter guesses [k_theta; b_theta]
        P = 1e3 * eye(2);      % Initial covariance matrix
        initialized = true;
    end
    
    % Algorithm Parameters
    lambda = 0.995;            % Forgetting factor
    theta_wall = 0.0;          % Virtual wall boundary angle (rad)
    J = 0.05;                  % Device rotational inertia (kg*m^2)
    
    theta_err = theta - theta_wall;
    
    % 1. Deadzone filter: Ignore updates when near zero to prevent division by small numbers / explosion
    deadzone_threshold = 0.005; % rad (approx 0.28 degrees)
    
    if theta_err < -deadzone_threshold && abs(omega) > 1e-2
        % Regressor vector phi
        phi = [theta_err * omega; omega^2];
        
        % Output measurement y = Input Power - Kinetic Power Change
        y = tau_h * omega - J * omega * alpha_acc;
        
        % 2. Normalization / Covariance clamping to prevent exponential growth
        denominator = lambda + phi' * P * phi;
        
        % Only update if the denominator is safely above zero
        if denominator > 1e-4
            k_gain = P * phi / denominator;
            theta_est = theta_est + k_gain * (y - phi' * theta_est);
            
            % Update covariance and bound P to prevent windup/explosion
            P_new = (P - k_gain * phi' * P) / lambda;
            
            % Trace or max eigenvalue check to clamp P if it grows too large
            if trace(P_new) < 1e6
                P = P_new;
            else
                P = 1e3 * eye(2); % Reset covariance if it starts blowing up
            end
        end
    end
    
    % Enforce positive physical limits on estimated rotational parameters
    k_theta_est = max(0, theta_est(1));
    b_theta_est = max(0, theta_est(2));
end
