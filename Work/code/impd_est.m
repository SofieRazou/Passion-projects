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

function impd_est = fcn(near_zero, n_crossing, torque, angle, fact)

% Small regularization parameter
epsilon = 1e-4;

% Shift angle around the zero crossing
angle_shift = angle - n_crossing*pi;

% Regularized estimates
impd_zero = fact * angle_shift / (angle_shift^2 + epsilon^2);
impd_torque = torque * angle / (angle^2 + epsilon^2);

% Smooth transition
if near_zero
    impd_est = impd_zero;
else
    impd_est = impd_torque;
end

end
