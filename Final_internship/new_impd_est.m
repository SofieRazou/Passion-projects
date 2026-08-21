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
    J = 0.05;                  % Device rotational inertia / moment of inertia (kg*m^2)
    
    theta_err = theta - theta_wall;
    
    % Run RLS update only during active rotational wall penetration and non-zero velocity
    if theta_err < 0 && abs(omega) > 1e-3
        % Regressor vector phi = [theta_err * omega; omega^2]
        phi = [theta_err * omega; omega^2];
        
        % Output measurement y = Input Power - Kinetic Power Change (Rotational)
        y = tau_h * omega - J * omega * alpha_acc;
        
        % Recursive Least Squares gain and update
        k_gain = P * phi / (lambda + phi' * P * phi);
        theta_est = theta_est + k_gain * (y - phi' * theta_est);
        P = (P - k_gain * phi' * P) / lambda;
    end
    
    % Enforce positive physical limits on estimated rotational parameters
    k_theta_est = max(0, theta_est(1));
    b_theta_est = max(0, theta_est(2));
end
