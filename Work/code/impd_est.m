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
function [impd_est, impd_reg_est] = fcn(near_zero, n_crossing, torque, angle, fact)

x = angle - n_crossing*pi;

x_min = 1e-3;

if near_zero
    
    if abs(x) > x_min
        % Cotangent approximation
        impd_est = fact*(1/x - x/3);
    else
        % Limit the impedance close to the singularity
        impd_est = fact*(1/x_min - x_min/3)*sign(x);
    end
    
    impd_reg_est = 30;

else
    
    impd_est = 1.816;
    
    if abs(angle) > x_min
        impd_reg_est = torque/angle;
    else
        impd_reg_est = 30;
    end
    
end

end
