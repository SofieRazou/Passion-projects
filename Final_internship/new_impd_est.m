% Live Impedance Estimator and Energy Cycle Regulator Simulation
% Based on the logic from Dinc et al., 2024[cite: 1]

clear; clc; close all;

%% Simulation Parameters
dt = 0.001;          % Sampling period (1 ms)[cite: 1]
T_total = 2.0;       % Total simulation time (s)
N_steps = round(T_total / dt);

% System & Environment Parameters
m = 0.5;             % Haptic device inertia (kg)[cite: 1]
k_desired = 12000;   % Desired virtual wall stiffness (N/m)[cite: 1]
x_wall = 0;          % Virtual wall position (m)

% Preallocation of variables
t = zeros(N_steps, 1);
x = zeros(N_steps, 1);
v = zeros(N_steps, 1);
F_h = zeros(N_steps, 1);
F_wall = zeros(N_steps, 1);
E_tot = zeros(N_steps, 1);
alpha_c = zeros(N_steps, 1);

% Time-window buffer for cycle detection (5 steps: 2 prev, current, 2 future)[cite: 1]
energy_buffer = zeros(5, 1);
buffer_idx = 1;

% State tracking variables
current_cycle = 1;
E_cycle_end = 0;
E_prev_cycle = 0;
E_gen = 0;
current_alpha = 0;
sum_v2_dt = 0;

%% Main Simulation Loop
for n = 2:N_steps
    t(n) = (n - 1) * dt;
    
    % Simulate Human Force Input (e.g., pushing into the wall and releasing)
    if t(n) > 0.2 && t(n) < 1.5
        F_h(n) = 15 * sin(2 * pi * 3 * (t(n) - 0.2)); 
    else
        F_h(n) = 0;
    end
    
    % Position error calculation (penetration inside virtual wall when x < x_wall)
    x_err = x(n-1) - x_wall;
    
    % Virtual wall reaction force with adaptive damping control
    if x_err < 0
        F_wall(n) = -k_desired * x_err - current_alpha * v(n-1);
    else
        F_wall(n) = 0;
        current_alpha = 0; % Reset damping outside the wall
    end
    
    % Plant Dynamics (Acceleration -> Velocity -> Position)
    accel = (F_h(n) - F_wall(n)) / m;
    v(n) = v(n-1) + accel * dt;
    x(n) = x(n-1) + v(n) * dt;
    
    % Instantaneous Net Energy Observation[cite: 1]
    power_inst = F_wall(n) * v(n);
    if n == 2
        E_tot(n) = power_inst * dt;
    else
        E_tot(n) = E_tot(n-1) + power_inst * dt;
    end
    
    % Shift energy into the time-window buffer[cite: 1]
    energy_buffer = circshift(energy_buffer, -1);
    energy_buffer(5) = E_tot(n);
    
    % Check for Energy Cycle Completion using Time-Window Filter[cite: 1]
    % Condition: E(t-2) > E(t-1) > E(t) < E(t+1) < E(t+2)
    if energy_buffer(1) > energy_buffer(2) && ...
       energy_buffer(2) > energy_buffer(3) && ...
       energy_buffer(3) < energy_buffer(4) && ...
       energy_buffer(4) < energy_buffer(5)
       
        % Actual energy cycle detected at buffer(3)
        E_cycle_end = energy_buffer(3);
        
        if current_cycle > 1
            % Estimate generated energy between consecutive cycles[cite: 1]
            E_gen = E_cycle_end - E_prev_cycle;
            
            % Compute updated adaptive damping for the upcoming cycle[cite: 1]
            if E_gen > 0 && sum_v2_dt > 0
                current_alpha = current_alpha + (E_gen / sum_v2_dt);
            end
        end
        
        E_prev_cycle = E_cycle_end;
        current_cycle = current_cycle + 1;
        sum_v2_dt = 0; % Reset velocity accumulator for next cycle
    end
    
    % Accumulate squared velocity terms for adaptive damping denominator[cite: 1]
    if x_err < 0
        sum_v2_dt = sum_v2_dt + (v(n)^2 * dt);
    end
    
    alpha_c(n) = current_alpha;
end

%% Plotting Results
figure('Name', 'Live Impedance Estimator & Energy Cycle Regulator', 'Position', [100, 100, 900, 700]);

subplot(4, 1, 1);
plot(t, x * 1e3, 'LineWidth', 1.5);
ylabel('Penetration (mm)');
title('Virtual Wall Haptic Interaction with Cycle-Based Regulation[cite: 1]');
grid on;

subplot(4, 1, 2);
plot(t, E_tot * 1e3, 'Color', 'b', 'LineWidth', 1.2);
ylabel('Energy (mJ)');
grid on;

subplot(4, 1, 3);
plot(t, alpha_c, 'Color', 'r', 'LineWidth', 1.5);
ylabel('Adaptive Damping (\alpha_c)');
grid on;

subplot(4, 1, 4);
plot(t, F_wall, 'Color', 'k', 'LineWidth', 1.2);
xlabel('Time (s)');
ylabel('Wall Force (N)');
grid on;
