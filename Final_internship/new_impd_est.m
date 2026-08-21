function [a1, a2, b1, b2] = BlackBox_TF_Estimator(torque, angle, dt)
%#codegen
% BLACK-BOX TRANSFER FUNCTION ESTIMATOR (ARX MODEL)
% Estimates generic 2nd-order polynomial coefficients mapping Torque -> Angle
% Model: angle[k] = -a1*angle[k-1] - a2*angle[k-2] + b1*torque[k-1] + b2*torque[k-2]

%% Persistent Estimator States
persistent theta_vec P lambda_r

%% Initialization
if isempty(theta_vec)
    theta_vec = zeros(4, 1);     % Parameters [a1; a2; b1; b2]
    P         = 100.0 * eye(4);  % Covariance matrix
    lambda_r  = 0.99;            % Forgetting factor
end

%% Persistent Delay Buffers (Past inputs and outputs)
persistent y_1 y_2 u_1 u_2
if isempty(y_1)
    y_1 = 0.0; y_2 = 0.0;
    u_1 = 0.0; u_2 = 0.0;
end

%% 1. Build Regressor Vector from Past Inputs (Torque) and Outputs (Angle)
% phi = [-y[k-1]; -y[k-2]; u[k-1]; u[k-2]]
phi = [-y_1; -y_2; u_1; u_2];

%% 2. RLS Update with Singularity Protection
reg_energy = phi' * phi;
epsilon_reg = 1e-5;

if reg_energy > epsilon_reg
    % Prediction and Error
    y_pred = phi' * theta_vec;
    e_error = angle - y_pred;
    
    % Denominator
    den = lambda_r + phi' * P * phi;
    
    if abs(den) > 1e-8
        % Kalman Gain
        K = (P * phi) / den;
        
        % Parameter Update
        theta_vec = theta_vec + K * e_error;
        
        % Covariance Update (Joseph form for numerical stability)
        P_temp = (eye(4) - K * phi') * P;
        P = (P_temp + P_temp') / 2.0;
        P = P / lambda_r;
    end
end

%% 3. Update Delay Buffers for Next Step
y_2 = y_1;
y_1 = angle;
u_2 = u_1;
u_1 = torque;

%% 4. Extract Black-Box Coefficients
a1 = theta_vec(1);
a2 = theta_vec(2);
b1 = theta_vec(3);
b2 = theta_vec(4);

end
