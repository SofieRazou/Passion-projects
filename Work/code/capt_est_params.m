clear
close all
clc

%% =============================================================
%                  KNOWN PHYSICAL PARAMETERS
% =============================================================
J_known = 0.0103; % Motor inertia [kg*m^2] (Fixed)

%% =============================================================
%                   LOAD AND PREPARE DATA
% =============================================================
if ~exist('exp_sorted.mat', 'file')
    error('exp_sorted.mat not found! Run the extraction script first.');
end

load('exp_sorted.mat'); 

% Identify individual segments based on time resets
time_vec      = exp_sorted(:, 3);
seg_breaks    = find(diff(time_vec) < 0);
start_indices = [1; seg_breaks + 1];
end_indices   = [seg_breaks; length(time_vec)];

num_total_segments = length(start_indices);
fprintf('Found %d individual segments to analyze.\n\n', num_total_segments);

% Preallocate arrays for summary results
b_est_all   = zeros(num_total_segments, 1);
k_est_all   = zeros(num_total_segments, 1);
fit_perc_all = zeros(num_total_segments, 1);

%% =============================================================
%              LOOP THROUGH EACH EXPERIMENT SEGMENT
% =============================================================
for s = 1:num_total_segments
    % Extract current segment
    idx       = start_indices(s):end_indices(s);
    seg_angle = exp_sorted(idx, 1); % Column 1: Angle (deg)
    seg_load  = exp_sorted(idx, 2); % Column 2: Measured Torque (Nm)
    seg_time  = exp_sorted(idx, 3); % Column 3: Time (s)
    
    Ts = mean(diff(seg_time));
    
    % Signal Preprocessing: Zero-mean and convert angle to radians
    u = detrend(seg_load(:));               % Input torque tau [Nm]
    y = detrend(deg2rad(seg_angle(:)));     % Output angle theta [rad]
    
    % ----------------------------------------------------------
    % FILTERED DIFFERENTIATION FOR VELOCITY & ACCELERATION
    % ----------------------------------------------------------
    % Use a low-pass central difference to prevent high-frequency noise amplification
    fc = 20; % Low-pass cutoff frequency [Hz]
    [b_flt, a_flt] = butter(2, fc * (2 * Ts), 'low');
    
    % Filtered angle
    y_flt = filtfilt(b_flt, a_flt, y);
    
    % Velocity (theta_dot) and Acceleration (theta_ddot)
    dtheta    = gradient(y_flt) / Ts;
    ddtheta   = gradient(dtheta) / Ts;
    
    % ----------------------------------------------------------
    % DIRECT GREY-BOX LEAST-SQUARES ESTIMATION
    % ----------------------------------------------------------
    % Y_known = tau - J * theta_ddot
    Y_known = u - J_known * ddtheta;
    
    % Regressor matrix X = [theta_dot, theta]
    X_reg = [dtheta, y_flt];
    
    % Solve for parameters theta_param = [b; kappa]
    params = X_reg \ Y_known;
    
    b_est = params(1);
    k_est = params(2);
    
    % ----------------------------------------------------------
    % MODEL VALIDATION & FIT PERCENTAGE
    % ----------------------------------------------------------
    % Construct continuous-time state-space model with estimated b and k
    A_mat = [0, 1; -k_est/J_known, -b_est/J_known];
    B_mat = [0; 1/J_known];
    C_mat = [1, 0];
    D_mat = 0;
    
    sys_est = ss(A_mat, B_mat, C_mat, D_mat);
    data_id = iddata(y, u, Ts);
    
    [~, fit_val] = compare(data_id, sys_est);
    
    % Store metrics
    b_est_all(s)    = b_est;
    k_est_all(s)    = k_est;
    fit_perc_all(s) = fit_val;
    
    % Plot Comparison
    figure('Name', sprintf('Segment %d Direct Grey-Box', s));
    compare(data_id, sys_est);
    grid on;
    title(sprintf('Segment %d: Fit = %.1f%% | Damping b = %.4f Nms/rad | Stiffness \\kappa = %.4f Nm/rad', ...
        s, fit_val, b_est, k_est));
    drawnow;
end

%% =============================================================
%                   PRINT SUMMARY RESULTS
% =============================================================
Segment_ID   = (1:num_total_segments)';
SummaryTable = table(Segment_ID, b_est_all, k_est_all, fit_perc_all, ...
    'VariableNames', {'Segment', 'Damping_b_Nms_rad', 'Stiffness_kappa_Nm_rad', 'Fit_Percent'});

disp('========================================================================');
disp('          DIRECT PHYSICAL GREY-BOX ESTIMATION RESULTS                   ');
disp('========================================================================');
disp(SummaryTable);

% Overall Averages
fprintf('\n--- OVERALL AVERAGES ACROSS %d SEGMENTS ---\n', num_total_segments);
fprintf('Average Damping (b)         : %.6f N*m*s/rad\n', mean(b_est_all));
fprintf('Average Stiffness (kappa/k) : %.6f N*m/rad\n', mean(k_est_all));
fprintf('Average Model Fit           : %.2f%%\n', mean(fit_perc_all));
