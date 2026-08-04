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

function [impd_est, impd_reg_est] = fcn(near_zero, n_crossing, torque, angle, fact)
%#codegen
% NATURAL REGULARIZED IMPEDANCE (KAPPA) ESTIMATOR
%
% Prevents large impedance spikes (e.g., 500+) by smoothly approximating
% stiffness kappa across zero crossings using bounded regularized regression.

%% 1. Physical Parameters
kappa_0 = 1.816;      % Nominal baseline stiffness kappa [N*m/rad]
kappa_max = 30.0;     % Maximum physical stiffness cap [N*m/rad]
kappa_min = 0.1;      % Minimum physical stiffness floor [N*m/rad]

epsilon = 0.05;       % Regularization tuning factor (prevents 1/0 singularities)
angle_width = 0.05;   % Zero-crossing boundary layer width [rad] (~3 degrees)

%% 2. Shifted Angle Calculation
angle_shift = angle - n_crossing * pi;

%% 3. Smooth Regularized Stiffness (Kappa) Approximation
% Regularized formula: (Torque * Angle + kappa_0 * epsilon) / (Angle^2 + epsilon)
% Guarantees impd -> kappa_0 smoothly as angle -> 0
num_zero   = (fact * abs(angle_shift)) + (kappa_0 * epsilon);
den_zero   = (angle_shift^2) + epsilon;
kappa_zero = num_zero / den_zero;

num_torque   = (torque * angle) + (kappa_0 * epsilon);
den_torque   = (angle^2) + epsilon;
kappa_torque = num_torque / den_torque;

%% 4. Continuous Smooth Blending (Exponential Weighting)
% Smooth weight w: 0 near zero crossings, 1 far away from zero
w_zero   = 1.0 - exp(-(angle_shift / angle_width)^2);
w_torque = 1.0 - exp(-(angle / angle_width)^2);

% Blend between baseline stiffness kappa_0 and measured kappa
impd_zero_blend   = (1.0 - w_zero) * kappa_0 + w_zero * kappa_zero;
impd_torque_blend = (1.0 - w_torque) * kappa_0 + w_torque * kappa_torque;

%% 5. Select & Cap Outputs
if near_zero
    impd_est     = impd_zero_blend;
    impd_reg_est = kappa_max;
else
    impd_est     = impd_torque_blend;
    impd_reg_est = impd_torque_blend;
end

% Enforce hard physical bounds [kappa_min, kappa_max]
impd_est     = min(max(impd_est, kappa_min), kappa_max);
impd_reg_est = min(max(impd_reg_est, kappa_min), kappa_max);

end
