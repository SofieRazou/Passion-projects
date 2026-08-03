function [impd_est, impd_reg_est] = fcn(near_zero, n_crossing,torque, angle, fact)

%Boolean cut for impedance estimation near zero
if near_zero
    impd_est = fact/(angle-n_crossing*pi);
    impd_reg_est = 30;
else
    impd_est = 1.816;
    impd_reg_est = torque/angle;
    
end 
end 
