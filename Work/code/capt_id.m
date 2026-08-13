function [time_data, angle_data, torque_data] = capt_id

% =============================================================
% 1. PURE STIFFNESS (k-only) THEORETICAL TRANSFER FUNCTION & BODE
% =============================================================
J_val = 0.0103;            % Fixed motor inertia
k_avg = 42.95 + 1;         % Average estimated stiffness
b_avg = 9.1079;

num = [1];
den = [J_val, b_avg, k_avg]; 
sys_k_only = tf(num, den);

disp('--- PURE STIFFNESS TRANSFER FUNCTION (b=0) ---');
disp(sys_k_only);

% Plot Theoretical Bode Diagram
figure('Name', 'k-Only System Bode Diagram');
bode(sys_k_only);
grid on;
title(sprintf('Theoretical Bode Plot (k = %.2f, b = %.2f)', k_avg, b_avg))


% =============================================================
% EMPIRICAL MODEL & BODE PLOT (Post-processing Recorded Data)
% =============================================================
if length(time_data) > 10
    % Calculate uniform sample time
    Ts = mean(diff(time_data));
    
    % Create an iddata object (Input: Torque, Output: Angle/Out1)
    data = iddata(angle_data, torque_data, Ts);
    
    % Estimate transfer function model from recorded stream (Empirical)
    sys_empirical = tfest(data, 2, 1);
    
    % Generate the Empirical Bode Plot in a new figure window
    figure('Name', 'System Identification - Empirical Bode Plot', 'Position', [200, 200, 700, 500]);
    bode(sys_empirical);
    grid on;
    title('Bode Plot of Empirical dSPACE System');
    disp('Empirical Bode plot generated successfully.');
    
    % =============================================================
    %ACTUAL (THEORETICAL MODEL BASED ON MEASURED DATA) BODE PLOT
    % =============================================================
    % Build the actual/theoretical transfer function using your physical parameters
    % Input: Torque, Output: Angle
    sys_actual = tf([1], [J_val, b_avg, k_avg]);
    
    % Generate the Actual/Theoretical Bode Plot in a separate figure window
    figure('Name', 'System Identification - Actual Theoretical Bode Plot', 'Position', [300, 200, 700, 500]);
    bode(sys_actual);
    grid on;
    title(sprintf('Bode Plot of Actual Model (J=%.4f, b=%.4f, k=%.2f)', J_val, b_avg, k_avg));
    disp('Actual theoretical Bode plot generated successfully.');
else
    disp('Not enough data collected to generate reliable Bode plots.');
end
% =============================================================
% 3. DIRECT NON-PARAMETRIC BODE PLOT (Angle & Torque Measurements Only)
% =============================================================
if length(time_data) > 20
    % Calculate uniform sample time
    dt = mean(diff(time_data));
    Fs = 1 / dt; % Sampling frequency
    
    % Detrend data to remove any DC biases or offsets
    torque_clean = detrend(torque_data);
    angle_clean = detrend(angle_data);
    
    % Compute direct Frequency Response Estimate (FRF) using Welch's method
    % This divides the angle/torque data into windows to calculate the direct ratio
    [H, freq_vector] = tfestimate(torque_clean, angle_clean, [], [], [], Fs);
    
    % Convert frequency vector from Hz to rad/s for standard Bode plotting
    omega = freq_vector * 2 * pi;
    
    % Convert magnitude to decibels (dB) and phase to degrees
    mag_dB = 20 * log10(abs(H));
    phase_deg = unwrap(angle(H)) * (180 / pi);
    
    % Plot the Direct Measured Bode Diagram
    figure('Name', 'Direct Measured Bode Plot (Angle vs Torque)', 'Position', [200, 200, 700, 600]);
    
    subplot(2,1,1);
    semilogx(omega, mag_dB, 'b-', 'LineWidth', 1.5);
    grid on;
    grid minor;
    ylabel('Magnitude (dB)');
    title('Direct Empirical Bode Plot from Measured Angle & Torque');
    
    subplot(2,1,2);
    semilogx(omega, phase_deg, 'r-', 'LineWidth', 1.5);
    grid on;
    grid minor;
    xlabel('Frequency (rad/s)');
    ylabel('Phase (deg)');
    
    disp('Direct non-parametric Bode plot generated successfully from raw measurements.');
else
    disp('Not enough data collected to generate a reliable direct Bode plot.');
end

