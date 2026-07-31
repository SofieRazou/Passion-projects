function a = fcn(Eobs, omega)

persistent a_prev

%% Parameters
gamma = 0.05;          % adaptation gain (tune 0.01-0.2)
omega_min = 1e-3;      % avoid division by zero

a_min = 0.05;          % minimum damping
a_max = 5.0;           % maximum damping

%% Initialization
if isempty(a_prev)
    a_prev = a_min;
end

%% Safe velocity
omega_safe = max(abs(omega), omega_min);

%% Adaptation

if Eobs < 0

    % Increase damping when passivity is violated
    da = -gamma * Eobs / (omega_safe^2 + 1e-6);

    a = a_prev + da;

else

    % Slowly relax damping toward minimum
    relaxation = 0.01;

    a = a_prev - relaxation*(a_prev-a_min);

end

%% Saturation
a = min(max(a,a_min),a_max);

%% Save state
a_prev = a;

end
