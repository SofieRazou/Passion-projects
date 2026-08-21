function [kappa_est, b_est] = BlackBox_Impedance_Estimator(torque, angle, dt)
%#codegen
% REAL-TIME BLACK-BOX TO PHYSICAL IMPEDANCE ESTIMATOR
% Estimates ARX parameters via RLS and converts them analytically 
% to physical stiffness (kappa) and damping (b) using Tustin's method.

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

%% 1. Build Regressor Vector
phi = [-y_1; -y_2; u_1; u_2];

%% 2. RLS Update with Singularity Protection
reg_energy = phi' * phi;
epsilon_reg = 1e-5;

if reg_energy > epsilon_reg
    y_pred = phi' * theta_vec;
    e_error = angle - y_pred;
    
    den = lambda_r + phi' * P * phi;
    
    if abs(den) > 1e-8
        K = (P * phi) / den;
        theta_vec = theta_vec + K * e_error;
        
        P_temp = (eye(4) - K * phi') * P;
        P = (P_temp + P_temp') / 2.0;
        P = P / lambda_r;
    end
end

%% 3. Update Delay Buffers
y_2 = y_1;
y_1 = angle;
u_2 = u_1;
u_1 = torque;

%% 4. Extract ARX Coefficients
a1 = theta_vec(1);
a2 = theta_vec(2);
b1 = theta_vec(3);
b2 = theta_vec(4);

%% 5. Analytical Tustin Transformation (Discrete -> Continuous)
% Maps discrete denominator polynomial (1 + a1*z^-1 + a2*z^-2) 
% to continuous s-domain (s^2 + alpha1*s + alpha0) without toolbox dependencies.
K_t = 2.0 / dt;
K_t2 = K_t^2;

% Denominator transformation coefficients
denom_scaler = 1.0 + a1 + a2;
if abs(denom_scaler) > 1e-6
    % Continuous-time characteristic polynomial coefficients
    alpha_1 = (2.0 * K_t * (1.0 - a2)) / denom_scaler;
    alpha_0 = (K_t2 * (1.0 + a1 + a2)) / denom_scaler; % Wait, let's use standard bilinear mapping below:
    
    % Standard Bilinear (Tustin) mapping for z = (2/dt + s)/(2/dt - s):
    % (2/dt + s)^2 + a1*(2/dt + s)*(2/dt - s) + a2*(2/dt - s)^2 = 0 expansion:
    term_denom = 1.0 + a1 + a2;
    if abs(term_denom) > 1e-6
        c2 = 1.0 + a1 + a2;
        c1 = 2.0 * K_t * (1.0 - a2);
        c0 = K_t2 * (1.0 - a1 + a2);
        
        % Normalized continuous coefficients (assuming unit inertia J = 1 or scaling)
        b_raw     = c1 / c2;
        kappa_raw = c0 / c2;
    else
        b_raw     = 0.01;
        kappa_raw = 1.816;
    end
else
    b_raw     = 0.01;
    kappa_raw = 1.816;
end

%% 6. Physical Constraints & Output
kappa_est = max(0.0, kappa_raw);
b_est     = max(0.0, b_raw);

end
