function [kappa_est, b_est] = DREM_Inspired_Estimator(torque, angle, velocity, dt)
%#codegen
% ROBUST DECOUPLED IMPEDANCE ESTIMATOR (SINGULARITY-FREE)
% Avoids matrix inversions by filtering and processing signals independently.

%% Persistent Filters (States)
persistent F_tau_th F_th_th F_th_v F_tau_v F_v_v alpha kappa_prev b_prev

%% Initialization
if isempty(F_tau_th)
    F_tau_th = 0.0; % Filtered torque * angle
    F_th_th  = 0.0px; % Filtered angle^2
    F_th_v   = 0.0; % Filtered angle * velocity
    F_tau_v  = 0.0; % Filtered torque * velocity
    F_v_v    = 0.0; % Filtered velocity^2
    
    alpha    = 0.98; % Filter memory coefficient
    kappa_prev = 1.816;
    b_prev     = 0.01;
end

%% 1. Compute Instantaneous Cross-Products
tau_th = torque * angle;
th_th  = angle * angle;
th_v   = angle * velocity;
tau_v  = torque * velocity;
v_v    = velocity * velocity;

%% 2. Low-Pass Filter the Products (Continuous Integration)
F_tau_th = alpha * F_tau_th + (1 - alpha) * tau_th;
F_th_th  = alpha * F_th_th  + (1 - alpha) * th_th;
F_th_v   = alpha * F_th_v   + (1 - alpha) * th_v;
F_tau_v  = alpha * F_tau_v  + (1 - alpha) * tau_v;
F_v_v    = alpha * F_v_v    + (1 - alpha) * v_v;

%% 3. Decoupled Scalar Estimation with Safe Denominators
% Instead of a raw 2x2 matrix inversion prone to zero-crossing drops, 
% we compute independent directional estimates with a strict lower bound on energy.

epsilon_safe = 1e-4;

% Estimate stiffness (kappa) primarily when angle energy is active
if abs(F_th_th) > epsilon_safe
    % Cross-talk compensation using mixed terms
    kappa_candidate = (F_tau_th - F_th_v * b_prev) / F_th_th;
    kappa_est = kappa_candidate;
    kappa_prev = kappa_est;
else
    kappa_est = kappa_prev; % Hold last known good value near zero angle
end

% Estimate damping (b) primarily when velocity energy is active
if abs(F_v_v) > epsilon_safe
    b_candidate = (F_tau_v - F_th_v * kappa_prev) / F_v_v;
    b_est = b_candidate;
    b_prev = b_est;
else
    b_est = b_prev; % Hold last known good value near zero velocity
end

%% 4. Non-Negative Physical Constraints
kappa_est = max(0.0, kappa_est);
b_est     = max(0.0, b_est);

end
