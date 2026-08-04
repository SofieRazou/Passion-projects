(* function [impd_est, impd_reg_est] = fcn(near_zero, n_crossing,torque, angle, fact)

%Boolean cut for impedance estimation near zero
if near_zero
    impd_est = fact/(angle-n_crossing*pi);
    impd_reg_est = 30;
else
    impd_est = 1.816;
    impd_reg_est = torque/angle;
    
end 
end  *)

(*  *)
function [kappa_est, b_est] = Continuous_Impedance_Estimator(torque, angle, velocity, dt)
%#codegen
% CONTINUOUS DUAL-EKF IMPEDANCE ESTIMATOR FOR 1-DOF CAPT MOTOR
%
% Replaces standard algebraic/RLS division with an Extended Kalman Filter (EKF)
% state-space estimator based on Roveda & Piga (2021).
%
% Inputs:
%   torque   : Applied/commanded motor torque (tau_m) [N*m]
%   angle    : Measured position/angle (theta) [rad]
%   velocity : Measured/filtered angular velocity (omega) [rad/s]
%   dt       : Sampling time step [s]
%
% Outputs:
%   kappa_est : Estimated environment/active stiffness Ke [N*m/rad]
%   b_est     : Motor/environment viscous damping estimate [N*m*s/rad]

%% 1. Physical Parameters of CAPT Motor System
J = 0.005;     % Motor + load inertia [kg*m^2]
B = 0.010;     % Nominal motor viscous damping coefficient [N*m*s/rad]
theta_0 = 0.0; % Baseline reference contact point [rad]

%% 2. Persistent States for EKF 1 (Interaction Torque Estimator)
persistent x1 P1 Q1 R1
if isempty(x1)
    x1 = zeros(3, 1);              % State vector: [theta; omega; tau_ext]
    P1 = eye(3) * 0.1;             % State covariance
    Q1 = diag([1e-6, 1e-4, 1e-2]); % Process noise covariance
    R1 = diag([1e-6, 1e-4]);       % Measurement noise covariance
end

%% 3. Persistent States for EKF 2 (Stiffness Ke / Kappa Estimator)
persistent x2 P2 Q2 R2
if isempty(x2)
    x2 = [0.0; 0.0; 1.816];        % State vector: [theta; omega; Ke] (Initial Ke = 1.816)
    P2 = eye(3) * 1.0;             % State covariance
    Q2 = diag([1e-6, 1e-4, 1e-1]); % Process noise covariance
    R2 = diag([1e-6, 1e-4]);       % Measurement noise covariance
end

%% ==================== EKF 1: INTERACTION TORQUE ESTIMATOR ====================
% Predict Step (Euler Integration)
theta1   = x1(1);
omega1   = x1(2);
tau_ext1 = x1(3);

d_theta1   = omega1;
d_omega1   = (torque - B * omega1 - tau_ext1) / J;
d_tau_ext1 = 0.0;

x1_pred = x1 + [d_theta1; d_omega1; d_tau_ext1] * dt;

% Linearized State Jacobian Matrix F1 = df1/dx1
F1 = [ 0.0,      1.0,       0.0;
       0.0,   -B / J,   -1.0 / J;
       0.0,      0.0,       0.0 ];

% Covariance Prediction
A1 = eye(3) + F1 * dt;
P1_pred = A1 * P1 * A1' + Q1;

% Measurement Update
H1 = [1.0, 0.0, 0.0;
      0.0, 1.0, 0.0];
y1 = [angle; velocity] - H1 * x1_pred;
S1 = H1 * P1_pred * H1' + R1;
K1 = (P1_pred * H1') / S1;

x1 = x1_pred + K1 * y1;
P1 = (eye(3) - K1 * H1) * P1_pred;

tau_ext_est = x1(3);

%% ==================== EKF 2: STIFFNESS (KAPPA) ESTIMATOR ====================
tau_threshold = 0.02; % Contact detection threshold [N*m]

if abs(tau_ext_est) > tau_threshold
    theta2 = x2(1);
    omega2 = x2(2);
    Ke2    = x2(3);

    % Predict Step
    d_theta2 = omega2;
    d_omega2 = (torque - B * omega2 - Ke2 * (theta2 - theta_0)) / J;
    d_Ke2    = 0.0;

    x2_pred = x2 + [d_theta2; d_omega2; d_Ke2] * dt;

    % Linearized State Jacobian Matrix F2 = df2/dx2
    F2 = [ 0.0,               1.0,                     0.0;
          -Ke2 / J,        -B / J,  -(theta2 - theta_0) / J;
           0.0,               0.0,                     0.0 ];

    % Covariance Prediction
    A2 = eye(3) + F2 * dt;
    P2_pred = A2 * P2 * A2' + Q2;

    % Measurement Update
    H2 = [1.0, 0.0, 0.0;
          0.0, 1.0, 0.0];
    y2 = [angle; velocity] - H2 * x2_pred;
    S2 = H2 * P2_pred * H2' + R2;
    K2 = (P2_pred * H2') / S2;

    x2 = x2_pred + K2 * y2;
    P2 = (eye(3) - K2 * H2) * P2_pred;

    % Non-Negativity Physical Constraint on Stiffness
    x2(3) = max(0.0, x2(3));
else
    % Hold State when outside active interaction
    x2(1) = angle;
    x2(2) = velocity;
end

%% 4. Assign Output Arguments
kappa_est = x2(3); % Active stiffness estimate
b_est     = B;     % Calibrated viscous damping parameter

end
