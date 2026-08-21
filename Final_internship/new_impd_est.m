function [kappa_est, b_est] = Responsive_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% RESPONSIVE IMPEDANCE ESTIMATOR
% Smoothly tracks changes in kappa and b using torque, angle, and velocity.

%% Persistent Filter States
persistent F_tt F_tv F_vv F_tau_t F_tau_v kappa_curr b_curr alpha

%% Initialization
if isempty(F_tt)
    F_tt     = 0.0; 
    F_tv     = 0.0; 
    F_vv     = 0.0; 
    F_tau_t  = 0.0; 
    F_tau_v  = 0.0; 
    
    % A lower alpha (e.g., 0.90 to 0.95) allows the estimator to react 
    % much faster and change smoothly instead of freezing or staying flat.
    alpha    = 0.92; 
    
    kappa_curr = 1.816; % Initial guess
    b_curr     = 0.01;  % Initial guess
end

%% 1. Instantaneous Products from Model Variables
tt    = angle * angle;
tv    = angle * velocity;
vv    = velocity * velocity;
tau_t = torque * angle;
tau_v = torque * velocity;

%% 2. Fast Low-Pass Filtering (Sliding Window Effect)
F_tt     = alpha * F_tt    + (1 - alpha) * tt;
F_tv     = alpha * F_tv    + (1 - alpha) * tv;
F_vv     = alpha * F_vv    + (1 - alpha) * vv;
F_tau_t  = alpha * F_tau_t + (1 - alpha) * tau_t;
F_tau_v  = alpha * F_tau_v + (1 - alpha) * tau_v;

%% 3. Solve 2x2 System with Small Regularization for Smoothness
epsilon_reg = 1e-5; % Keeps matrix invertible without locking the values

A11 = F_tt + epsilon_reg;
A12 = F_tv;
A21 = F_tv;
A22 = F_vv + epsilon_reg;

det_A = (A11 * A22) - (A12 * A21);

if abs(det_A) > 1e-7
    inv_det = 1.0 / det_A;
    
    % Direct calculation working backward from the torque and model equations
    kappa_raw = inv_det * ( A22 * F_tau_t - A12 * F_tau_v);
    b_raw     = inv_det * (-A21 * F_tau_t + A11 * F_tau_v);
    
    % Smooth blending (Exponential smoothing on the output for silky transitions)
    smooth_factor = 0.2; % Higher = faster tracking, Lower = smoother
    kappa_curr = (1 - smooth_factor) * kappa_curr + smooth_factor * kappa_raw;
    b_curr     = (1 - smooth_factor) * b_curr     + smooth_factor * b_raw;
end

%% 4. Apply Physical Bounds
kappa_est = max(0.0, kappa_curr);
b_est     = max(0.0, b_curr);

end
