function [A,B,C,D,K,x0] = capt_init_model(J, b, k, Ts)
%HUMAN_INIT_MODEL Human rotational inertia-damping-stiffness model.
%
% Inputs:
%   J : capt known inertia
%   b : capt natural damping
%   k : capt natural stiffness
%   Ts : sample time supplied automatically by idgrey
%
% Input to model:
%   capt torque
%
% Output:
%   angular position

if J <= 0
    error("Motor inertia must be positive and non-zero.");
end

A = [0,       1;
    -k/J, -b/J];

B = [0;
     1/J];

C = [1, 0];
D = 0;

% No process-noise/disturbance model
K = zeros(2,1);

% Initial human states: [angle; angular velocity]
x0 = [0; 0];

% For a continuous-time model, Ts is normally zero.
% It is still required in the function signature.
end
