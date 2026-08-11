%% =============================================================
%        PURE STIFFNESS (k-only) TRANSFER FUNCTION & BODE
% =============================================================
J_val = 0.0103;          % Fixed motor inertia
k_avg = 42.95;           % Your average estimated stiffness

% Define Transfer Function with b = 0
num = [1];
den = [J_val, 0, k_avg]; % Notice the 0 for the damping coefficient term
sys_k_only = tf(num, den);

disp('--- PURE STIFFNESS TRANSFER FUNCTION (b=0) ---');
disp(sys_k_only);

% Plot Bode Diagram
figure('Name', 'k-Only System Bode Diagram');
bode(sys_k_only);
grid on;
title(sprintf('Bode Plot (Pure Stiffness: k = %.2f, b = 0)', k_avg));
