function [k_theta_est, b_theta_est] = fcn(tau_h, theta, omega, alpha_acc)
%#codegen

    % Persistent variables for RLS estimation memory
    persistent Theta P initialized
    
    % Configuration Parameters
    J = 0.0103;                % Device rotational inertia (kg*m^2)
    
    % Initialization on the first step
    if isempty(initialized)
        Theta = [0.0; 0.0];    % Initial parameter vector [k; b] starting at zero
        P = 100 * eye(2);      % Initial covariance matrix
        initialized = true;
    end
    
    % Default outputs to current estimates
    k_theta_est = Theta(1);
    b_theta_est = Theta(2);
    
    % Active motion and excitation check (prevents division by zero / noise drift)
    if abs(omega) > 0.005 || abs(theta) > 0.005
        
        % Regressor vector containing the independent variables [theta; omega]
        phi = [theta; omega];
        
        % Measured net torque available for spring and damper absorption
        y = tau_h - J * alpha_acc;
        
        % RLS Algorithm with Forgetting Factor (lambda)
        lambda = 0.98;         % Memory weighting (lower = faster tracking, higher = smoother)
        
        denominator = lambda + phi' * P * phi;
        
        if denominator > 1e-5
            % Compute Kalman-like gain vector
            K_gain = (P * phi) / denominator;
            
            % Prediction error based on current parameter guesses
            prediction_error = y - phi' * Theta;
            
            % Update parameter estimates [k; b]
            Theta = Theta + K_gain * prediction_error;
            
            % Update and bound covariance matrix P to prevent windup/explosion
            P_new = (P - K_gain * phi' * P) / lambda;
            if trace(P_new) < 1e5 && all(isfinite(P_new(:)))
                P = P_new;
            else
                P = 100 * eye(2); % Reset covariance safely if it tries to grow
            end
        end
        
    else
        % When inactive/stopped, gently leak/decay parameters back to zero
        decay = 0.02;
        Theta = Theta * (1 - decay);
    end
    
    % Strict physical bounding to guarantee meaningful and safe values
    k_theta_est = min(max(0, Theta(1)), 50000); % Bounded between 0 and 50,000 Nm/rad
    b_theta_est = min(max(0, Theta(2)), 200);   % Bounded between 0 and 200 Nms/rad
    
    % Final NaN/Inf safety net
    if ~isfinite(k_theta_est), k_theta_est = 0; end
    if ~isfinite(b_theta_est), b_theta_est = 0; end
    
    % Update persistent state vector
    Theta(1) = k_theta_est;
    Theta(2) = b_theta_est;
end
