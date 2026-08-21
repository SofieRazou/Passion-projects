function [k_est, b_est] = fcn(F_h, x, v, a, dt)
%#codegen

    % Persistent variables for RLS state persistence across simulation steps
    persistent theta P initialized
    
    % Initialization on the first step
    if isempty(initialized)
        theta = [1000; 5];     % Initial parameter guesses [k; b]
        P = 1e3 * eye(2);      % Initial covariance matrix
        initialized = true;
    end
    
    % Algorithm Parameters
    lambda = 0.995;            % Forgetting factor
    x_wall = 0.0;              % Virtual wall boundary position (m)
    m = 0.5;                   % Device mass matching the plant (kg)
    
    x_err = x - x_wall;
    
    % Run RLS update only during active wall penetration and non-zero velocity
    if x_err < 0 && abs(v) > 1e-3
        % Regressor vector phi = [x_err * v; v^2]
        phi = [x_err * v; v^2];
        
        % Output measurement y = Input Power - Kinetic Power Change
        y = F_h * v - m * v * a;
        
        % Recursive Least Squares gain and update
        k_gain = P * phi / (lambda + phi' * P * phi);
        theta = theta + k_gain * (y - phi' * theta);
        P = (P - k_gain * phi' * P) / lambda;
    end
    
    % Enforce positive physical limits on estimated parameters
    k_est = max(0, theta(1));
    b_est = max(0, theta(2));
end
