function [kappa_est, b_est] = Moment_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% METHOD OF MOMENTS WITH RIDGE REGULARIZATION (SINGULARITY-PROOF)
%
% Prevents matrix singularities during zero-crossings by adding a 
% small diagonal regularization factor.

%% Persistent Filters (States) for Moments
persistent M_tt M_tv M_vv M_tau_t M_tau_v alpha kappa_prev b_prev

%% Initialization
if isempty(M_tt)
    M_tt     = 0.0; 
    M_tv     = 0.0; 
    M_vv     = 0.0; 
    M_tau_t  = 0.0; 
    M_tau_v  = 0.0; 
    alpha    = 0.98; % Smoothing coefficient
    
    kappa_prev = 1.816;
    b_prev     = 0.01;
end

%% 1. Compute Instantaneous Products
tt    = angle * angle;
tv    = angle * velocity;
vv    = velocity * velocity;
tau_t = torque * angle;
tau_v = torque * velocity;

%% 2. Low-Pass Filter the Moments
M_tt     = alpha * M_tt    + (1 - alpha) * tt;
M_tv     = alpha * M_tv    + (1 - alpha) * tv;
M_vv     = alpha * M_vv    + (1 - alpha) * vv;
M_tau_t  = alpha * M_tau_t + (1 - alpha) * tau_t;
M_tau_v  = alpha * M_tau_v + (1 - alpha) * tau_v;

%% 3. Moment Matrix with Ridge Regularization (Prevents Singularities)
% Adding a tiny epsilon to the diagonal ensures the matrix is always invertible,
% even when angles/velocities cross zero and raw moments drop to 0.
epsilon_reg = 1e-4; 

A = [M_tt + epsilon_reg, M_tv; 
     M_tv,             M_vv + epsilon_reg];
 
b_vec = [M_tau_t; 
         M_tau_v];

%% 4. Stable 2x2 Analytical Solve
det_A = A(1,1)*A(2,2) - A(1,2)*A(2,1);

if abs(det_A) > 1e-8
    inv_det = 1.0 / det_A;
    kappa_est = inv_det * ( A(2,2) * b_vec(1) - A(1,2) * b_vec(2));
    b_est     = inv_det * (-A(2,1) * b_vec(1) + A(1,1) * b_vec(2));
    
    % Update memory of last good estimates
    kappa_prev = kappa_est;
    b_prev     = b_est;
else
    % Fallback to last valid state if severely ill-conditioned
    kappa_est = kappa_prev;
    b_est     = b_prev;
end

%% 5. Non-Negative Physical Constraints
kappa_est = max(0.0, kappa_est);
b_est     = max(0.0, b_est);

end
