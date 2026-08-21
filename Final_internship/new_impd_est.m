function [kappa_est, b_est] = Moment_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% METHOD OF MOMENTS / FILTERED CORRELATION IMPEDANCE ESTIMATOR
%
% Estimates stiffness (kappa) and damping (b) using low-pass filtered 
% moments, completely avoiding RLS matrix inversions and zero-crossing singularities.

%% Persistent Filters (States) for Moments
persistent M_tt M_tv M_vv M_tau_t M_tau_v alpha

%% Initialization
if isempty(M_tt)
    % Initialize low-pass filtered moment accumulators
    M_tt     = 0.0; % Moment of angle^2
    M_tv     = 0.0; % Moment of angle * velocity
    M_vv     = 0.0; % Moment of velocity^2
    M_tau_t  = 0.0; % Moment of torque * angle
    M_tau_v  = 0.0; % Moment of torque * velocity
    
    % Filter smoothing coefficient (determines memory window length)
    % Higher (e.g., 0.99) = smoother, slower tracking; Lower = faster tracking
    alpha    = 0.98; 
end

%% 1. Compute Instantaneous Products (Raw Moments)
tt  = angle * angle;
tv  = angle * velocity;
vv  = velocity * velocity;
tau_t = torque * angle;
tau_v = torque * velocity;

%% 2. Low-Pass Filter the Moments (Exponential Moving Average)
% This replaces instantaneous division with integrated historical correlation
M_tt     = alpha * M_tt    + (1 - alpha) * tt;
M_tv     = alpha * M_tv    + (1 - alpha) * tv;
M_vv     = alpha * M_vv    + (1 - alpha) * vv;
M_tau_t  = alpha * M_tau_t + (1 - alpha) * tau_t;
M_tau_v  = alpha * M_tau_v + (1 - alpha) * tau_v;

%% 3. Construct the 2x2 Moment Matrix and Solve
% Equation: [M_tt, M_tv; M_tv, M_vv] * [kappa; b] = [M_tau_t; M_tau_v]
A = [M_tt, M_tv; 
     M_tv, M_vv];
 
b_vec = [M_tau_t; 
         M_tau_v];

% Check determinant to ensure the matrix is well-conditioned (has enough motion excitation)
det_A = A(1,1)*A(2,2) - A(1,2)*A(2,1);

persistent kappa_prev b_prev
if isempty(kappa_prev)
    kappa_prev = 1.816;
    b_prev     = 0.01;
end

if abs(det_A) > 1e-6
    % Solve 2x2 system analytically (avoids heavy matrix inverse overhead)
    inv_det = 1.0 / det_A;
    kappa_est = inv_det * ( A(2,2) * b_vec(1) - A(1,2) * b_vec(2));
    b_est     = inv_det * (-A(2,1) * b_vec(1) + A(1,1) * b_vec(2));
    
    % Store valid estimates
    kappa_prev = kappa_est;
    b_prev     = b_est;
else
    % Hold last known good values during zero-motion or static periods
    kappa_est = kappa_prev;
    b_est     = b_prev;
end

%% 4. Non-Negative Physical Constraints
kappa_est = max(0.0, kappa_est);
b_est     = max(0.0, b_est);

end
