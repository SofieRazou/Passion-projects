function [kappa_est, b_est] = Continuous_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% CONTINUOUS RECURSIVE LEAST SQUARES (RLS) IMPEDANCE ESTIMATOR
%
% Dynamically estimates stiffness (kappa) and damping (b) anywhere in the workspace
% without division-by-zero, singular spikes, or zero-crossing distortion.

%% Persistent Estimator States
persistent theta_vec    % Parameter vector [kappa; b]
persistent P            % Estimation covariance matrix (2x2)
persistent lambda_r     % Forgetting factor (0.95 to 0.99)

%% Initialization
if isempty(theta_vec)
    theta_vec = [1.816; 0.01]; % Initial guess for [kappa; b]
    P         = 10.0 * eye(2); % Initial uncertainty matrix
    lambda_r  = 0.98;          % Exponential forgetting factor
end

%% 1. Regressor Matrix (Phi = [angle, velocity])
phi = [angle; velocity];

%% 2. Prediction Error
% Measured torque vs model-predicted torque
torque_pred = phi' * theta_vec;
e_error     = torque - torque_pred;

%% 3. Dynamic Gain & Covariance Update
% Regressor energy check: update ONLY when there is motion/displacement
reg_energy = phi' * phi;

if reg_energy > 1e-8
    % Kalman Gain update: K = P * phi / (lambda + phi' * P * phi)
    den = lambda_r + phi' * P * phi;
    K   = (P * phi) / den;
    
    % Parameter update
    theta_vec = theta_vec + K * e_error;
    
    % Covariance update (P = (I - K*phi')*P / lambda)
    P = (eye(2) - K * phi') * P / lambda_r;
    
    % Enforce Covariance Bounding (prevents estimator covariance blow-up)
    if trace(P) > 500
        P = 10.0 * eye(2);
    end
end

%% 4. Non-Negative Physical Constraints
% Stiffness kappa and damping b must remain non-negative
theta_vec(1) = max(0.0, theta_vec(1)); % kappa >= 0
theta_vec(2) = max(0.0, theta_vec(2)); % b >= 0

%% 5. Output Extraction
kappa_est = theta_vec(1);
b_est     = theta_vec(2);

end
