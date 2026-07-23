%Ackermann kinematics for ego car actor 
%defined sample rate: 1ms?
%theta == heading angle
%delta == commanded by the Motor steering angle 
function [x,y] = run_driving_venv(delta, theta, u, L, x_0, y_0, time_step)
    R = L/tan(delta);
    deltaS  = u*time_step;
    x = x_0 + R*(sin(theta + deltaS/L) - sin(theta));
    y = y_0 + R*(cos(theta) - cos(theta + deltaS/L));
end

