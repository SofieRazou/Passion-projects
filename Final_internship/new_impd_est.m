function [kappa_est, b_est] = TransferFunction_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% TRANSFER FUNCTION MODEL-BASED IMPEDANCE ESTIMATOR (USING STATE-VARIABLE FILTERS)
% Estimates kappa and b by matching filtered torque to a 2nd-order transfer function model.

%% Persistent States for Filtered Signals (Simulating Continuous Transfer Functions)
persistent z1_tau z2_tau z1_th z2_th kappa_prev b_prev

%% Initialization
if isempty(z1_tau)
    z1_tau = 0.0; z2_tau = 0.0;
    z1_th  = 0.0; z2_th  = 0.0;
    
    kappa_prev = 1.816;
    b_prev     = 0.01;
end

%% 1. Define Filter Transfer Function Parameters (Cutoff frequency omega_c)
% This acts as our modulating transfer function to clean up derivatives
omega_c = 50.0; % Filter bandwidth (rad/s)
alpha1  = 2 * omega_c;
alpha2  = omega_c^2;

%% 2. Apply State-Variable Filters (Continuous Transfer Function Simulation via Euler/Tustin)
% We filter torque and angle to get clean position, velocity, and acceleration estimates
% s^2 * X(s) -> filtered acceleration
% s * X(s)   -> filtered velocity
% X(s)       -> filtered position

% Filter Torque
dz1_tau = z2_tau;
dz2_tau = -alpha2 * z1_tau - alpha1 * z2_tau + torque;
z1_tau  = z1_tau + dz1_tau * dt;
z2_tau  = z2_tau + dz2_tau * dt;
tau_f   = z1_tau * alpha2; % Filtered torque

% Filter Angle
dz1_th  = z2_th;
dz2_th  = -alpha2 * z1_th - alpha1 * z2_th + angle;
z1_th   = z1_th + dz1_th * dt;
z2_th   = z2_th + dz2_th * dt;
th_f    = z1_th * alpha2;       % Filtered angle (x)
v_f     = z2_th * alpha2;       % Filtered velocity (dx/dt)
acc_f   = (-alpha2 * z1_th - alpha1 * z2_th) * alpha2; % Filtered acceleration (d2x/dt2)

%% 3. Work Backward from the Model Equation
% Model: Tau = J*acc + b*velocity + kappa*angle
% If we assume inertia J is known or small, we solve for kappa and b using the filtered signals:
% Tau_f = b * v_f + kappa * th_f  (ignoring inertia or including it if tracked)

% Construct matrix from filtered transfer function outputs
M11 = th_f * th_f;
M12 = th_f * v_f;
M22 = v_f * v_f;

R1  = tau_f * th_f;
R2  = tau_f * v_f;

det_M = (M11 * M22) - (M12 * M12);

epsilon_reg = 1e-4;
if abs(det_M) > epsilon_reg
    inv_det = 1.0 / (det_M + epsilon_reg);
    kappa_raw = inv_det * ( M22 * R1 - M12 * R2);
    b_raw     = inv_det * (-M12 * R1 + M11 * R2);
    
    % Smooth blending
    smooth = 0.15;
    kappa_prev = (1 - smooth) * kappa_prev + smooth * kappa_raw;
    b_prev     = (1 - smooth) * b_prev     + smooth * b_raw;
end

%% 4. Apply Physical Constraints
kappa_est = max(0.0, kappa_prev);
b_est     = max(0.0, b_prev);

end
