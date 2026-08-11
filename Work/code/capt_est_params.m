clear
close all
clc

%% =============================================================
%                    LOAD AND PREPARE DATA
% =============================================================
if ~exist('exp_sorted.mat', 'file')
    error('exp_sorted.mat not found!');
end

load('exp_sorted.mat'); 

% Identify individual segments based on time resets
time_vec      = exp_sorted(:, 3);
seg_breaks    = find(diff(time_vec) < 0);
start_indices = [1; seg_breaks + 1];
end_indices   = [seg_breaks; length(time_vec)];

num_total_segments = length(start_indices);
fprintf('Found %d individual segments to analyze.\n\n', num_total_segments);

% Preallocate summary result arrays
b_est_all  = zeros(num_total_segments, 1);
k_est_all  = zeros(num_total_segments, 1);
r2_all     = zeros(num_total_segments, 1);

% Cell arrays to store filtered data and parameters
seg_data_cell = cell(num_total_segments, 1);
params_cell   = cell(num_total_segments, 1);

%% =============================================================
%          LOOP 1: ESTIMATE PARAMETERS PER SEGMENT (WITH F_MAX)
% =============================================================
for s = 1:num_total_segments
    idx         = start_indices(s):end_indices(s);
    seg_angle   = exp_sorted(idx, 1); 
    seg_load    = exp_sorted(idx, 2); 
    seg_time    = exp_sorted(idx, 3); 
    
    Ts = mean(diff(seg_time));
    Fs = 1/Ts; 
    
    % Zero-mean signals
    raw_tau   = detrend(seg_load(:));
    raw_theta = detrend(deg2rad(seg_angle(:)));
    
    tau   = raw_tau - mean(raw_tau);
    theta = raw_theta - mean(raw_theta);
    
    % Check sign convention
    corr_val = corr(tau, theta);
    if corr_val < 0
        theta = -theta;
    end
    
    % Find max frequency (f_max) using FFT
    N = length(tau);
    Y = fft(tau);
    f_vec = (0:N-1)*(Fs/N);
    power_spec = abs(Y).^2 / N;
    
    half_idx = 1:floor(N/2);
    pos_freqs = f_vec(half_idx);
    pos_power = power_spec(half_idx);
    
    noise_threshold = max(pos_power) * 0.01;
    active_freqs = pos_freqs(pos_power > noise_threshold);
    if ~isempty(active_freqs)
        f_max = max(active_freqs);
    else
        f_max = 0.5; 
    end
    
    % Adaptive low-pass filter
    fc = max(f_max * 1.5, 1.0); 
    if fc >= (Fs / 2)
        fc = (Fs / 2) * 0.9; 
    end
    
    [b_flt, a_flt] = butter(2, fc / (Fs / 2), 'low');
    
    tau_flt   = filtfilt(b_flt, a_flt, tau);
    theta_flt = filtfilt(b_flt, a_flt, theta);
    
    dtheta = gradient(theta_flt) / Ts;
    
    % Non-negative least squares
    X_reg = [theta_flt, dtheta];
    params = lsqnonneg(X_reg, tau_flt);
    
    k_est = params(1); 
    b_est = params(2); 
    
    tau_pred = X_reg * params;
    SS_res = sum((tau_flt - tau_pred).^2);
    SS_tot = sum((tau_flt - mean(tau_flt)).^2);
    R2 = (1 - (SS_res / SS_tot)) * 100;
    
    k_est_all(s) = k_est;
    b_est_all(s) = b_est;
    r2_all(s)    = R2;
    
    params_cell{s}   = params;
    seg_data_cell{s} = struct('time', seg_time, 'theta', theta_flt, 'dtheta', dtheta, 'tau', tau_flt);
end

%% =============================================================
%    CROSS-VALIDATION: UNIQUE NON-REPEATED PAIRWISE TESTING
% =============================================================
if num_total_segments >= 2
    fprintf('\n========================================================================\n');
    fprintf('       NON-REPEATED PAIRWISE CROSS-VALIDATION MATRIX                    \n');
    fprintf('========================================================================\n');
    
    % Generate all possible unique pairs (Combinations without replacement)
    % nchoosek gives every unique unordered pair combination (e.g., [1,2], [1,3], [2,4]...)
    all_pairs = nchoosek(1:num_total_segments, 2);
    
    % Randomly shuffle the order of these pairs so they are non-sequential/random
    rng('shuffle');
    shuffled_indices = randperm(size(all_pairs, 1));
    all_pairs = all_pairs(shuffled_indices, :);
    
    % Loop through each random unique pair (Source vs Target)
    for p = 1:size(all_pairs, 1)
        src_seg = all_pairs(p, 1);
        tgt_seg = all_pairs(p, 2);
        
        % Extract parameters from Source Segment
        params_src = params_cell{src_seg};
        
        % Test on Target Segment
        t_data = seg_data_cell{tgt_seg};
        X_target = [t_data.theta, t_data.dtheta];
        tau_cross_pred = X_target * params_src;
        
        % Calculate Cross-Validation R^2
        SS_res_cv = sum((t_data.tau - tau_cross_pred).^2);
        SS_tot_cv = sum((t_data.tau - mean(t_data.tau)).^2);
        cross_R2 = (1 - (SS_res_cv / SS_tot_cv)) * 100;
        
        % Plot comparison for this unique pair
        figure('Name', sprintf('Pair Test: Model from Seg %d -> Tested on Seg %d', src_seg, tgt_seg));
        plot(t_data.time, t_data.tau, 'b', 'LineWidth', 1.5); hold on;
        plot(t_data.time, tau_cross_pred, 'r--', 'LineWidth', 1.5);
        grid on;
        xlabel('Time [s]');
        ylabel('Torque [Nm]');
        legend('Target Actual Torque', sprintf('Predicted Torque (Param from Seg %d)', src_seg), 'Location', 'Best');
        title(sprintf('Pairwise Test: Model Seg %d applied to Target Seg %d (Cross-R^2 = %.1f%%)', ...
            src_seg, tgt_seg, cross_R2));
        drawnow;
    end
    
    fprintf('Completed %d unique non-repeated pairwise cross-validation tests.\n', size(all_pairs, 1));
end



(* clear
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

% Preallocate summary result arrays
b_est_all  = zeros(num_total_segments, 1);
k_est_all  = zeros(num_total_segments, 1);
fit_tf_all = zeros(num_total_segments, 1);

%% =============================================================
%              LOOP THROUGH EACH EXPERIMENT SEGMENT
% =============================================================
for s = 1:num_total_segments
    % Extract current segment
    idx       = start_indices(s):end_indices(s);
    seg_angle = exp_sorted(idx, 1); % Column 1: Angle (deg)
    seg_load  = exp_sorted(idx, 2); % Column 2: Measured Torque (Nm)
    seg_time  = exp_sorted(idx, 3); % Column 3: Time (s)
    
    % Compute sampling time for this segment
    Ts = mean(diff(seg_time));
    
    % Zero-mean signals & convert angle to radians
    u = seg_load(:) - mean(seg_load(:));
    y = deg2rad(seg_angle(:) - mean(seg_angle(:)));
    
    % Create System Identification Data Object
    data_id = iddata(y, u, Ts);
    data_id.InputName  = {'Measured torque'};
    data_id.OutputName = {'Encoder angle'};
    data_id.InputUnit  = {'Nm'};
    data_id.OutputUnit = {'rad'};
    data_id.ExperimentName = {sprintf('Segment_%d', s)};
    
    % ----------------------------------------------------------
    % TRANSFER FUNCTION ESTIMATION (2 poles, 0 zeros)
    % ----------------------------------------------------------
    Gest = tfest(data_id, 2, 0);
    
    % Extract denominator coefficients: den = [1, a1, a0]
    [~, den] = tfdata(Gest, 'v');
    
    a1 = den(2);
    a0 = den(3);
    
    % Map to physical parameters using known inertia J
    b_est = a1 * J_known; % b = a1 * J
    k_est = a0 * J_known; % k = a0 * J
    
    % Calculate TF fit percentage
    [~, fit_tf] = compare(data_id, Gest);
    
    % Store metrics
    b_est_all(s)  = b_est;
    k_est_all(s)  = k_est;
    fit_tf_all(s) = fit_tf;
    
    % Plot comparison for this segment
    figure('Name', sprintf('Segment %d TF Fit', s));
    compare(data_id, Gest);
    grid on;
    title(sprintf('Segment %d TF Fit = %.1f%% (b = %.4f, k = %.4f)', ...
        s, fit_tf, b_est, k_est));
    set(findall(gcf, 'Type', 'Line'), 'LineWidth', 1.5);
    drawnow;
end

%% =============================================================
%                   PRINT SUMMARY RESULTS
% =============================================================
Segment_ID   = (1:num_total_segments)';
SummaryTable = table(Segment_ID, b_est_all, k_est_all, fit_tf_all, ...
    'VariableNames', {'Segment', 'Damping_b_Nms_rad', 'Stiffness_k_Nm_rad', 'TF_Fit_Percent'});

disp('========================================================================');
disp('          TRANSFER FUNCTION ESTIMATION WITH FIXED J RESULTS             ');
disp('========================================================================');
disp(SummaryTable);

% Overall Averages
fprintf('\n--- OVERALL AVERAGES ACROSS %d SEGMENTS ---\n', num_total_segments);
fprintf('Average Damping (b)  : %.6f N*m*s/rad\n', mean(b_est_all));
fprintf('Average Stiffness (k): %.6f N*m/rad\n', mean(k_est_all));
fprintf('Average Model Fit    : %.2f%%\n', mean(fit_tf_all)); *)

clear
close all
clc

%% =============================================================
%                   LOAD AND PREPARE DATA
% =============================================================
if ~exist('exp_sorted.mat', 'file')
    error('exp_sorted.mat not found!');
end

load('exp_sorted.mat'); 

% Identify individual segments based on time resets
time_vec      = exp_sorted(:, 3);
seg_breaks    = find(diff(time_vec) < 0);
start_indices = [1; seg_breaks + 1];
end_indices   = [seg_breaks; length(time_vec)];

num_total_segments = length(start_indices);
fprintf('Found %d individual segments to analyze.\n\n', num_total_segments);

% Preallocate summary result arrays
b_est_all  = zeros(num_total_segments, 1);
k_est_all  = zeros(num_total_segments, 1);
r2_all     = zeros(num_total_segments, 1);

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
    
    % Zero-mean signals
    tau   = detrend(seg_load(:));
    theta = detrend(deg2rad(seg_angle(:)));
    
    % ----------------------------------------------------------
    % CHECK SIGN CONVENTION (Phase/Direction Alignment)
    % ----------------------------------------------------------
    % Torque and angle MUST be positively correlated (torque pushes in + direction)
    corr_val = corr(tau, theta);
    if corr_val < 0
        % Invert angle to align sign convention
        theta = -theta;
    end
    
    % ----------------------------------------------------------
    % LOW-PASS FILTER BOTH SIGNALS EQUALLY (Zero Phase Lag)
    % ----------------------------------------------------------
    fc = 1.65; % Cutoff frequency [Hz]
    [b_flt, a_flt] = butter(2, fc * (2 * Ts), 'low');
    
    tau_flt   = filtfilt(b_flt, a_flt, tau);
    theta_flt = filtfilt(b_flt, a_flt, theta);
    
    % Compute velocity (theta_dot)
    dtheta = gradient(theta_flt) / Ts;
    
    % ----------------------------------------------------------
    % NON-NEGATIVE LEAST SQUARES (lsqnonneg)
    % Model: tau = k * theta + b * theta_dot
    % Form: A * x = B  =>  [theta, theta_dot] * [k; b] = tau
    % ----------------------------------------------------------
    X_reg = [theta_flt, dtheta];
    
    % Constrains x = [k; b] >= 0 strictly
    params = lsqnonneg(X_reg, tau_flt);
    
    k_est = params(1); % Stiffness [Nm/rad]
    b_est = params(2); % Damping [Nms/rad]
    
    % Predict torque and calculate Goodness of Fit (R^2)
    tau_pred = X_reg * params;
    SS_res = sum((tau_flt - tau_pred).^2);
    SS_tot = sum((tau_flt - mean(tau_flt)).^2);
    R2 = (1 - (SS_res / SS_tot)) * 100;
    
    % Store metrics
    k_est_all(s) = k_est;
    b_est_all(s) = b_est;
    r2_all(s)    = R2;
    
    % Plot response for current segment
    figure('Name', sprintf('Segment %d Alignment & Fit', s));
    subplot(2,1,1);
    plot(seg_time, tau_flt, 'b', 'LineWidth', 1.5); hold on;
    plot(seg_time, tau_pred, 'r--', 'LineWidth', 1.5);
    grid on;
    ylabel('Torque [Nm]');
    legend('Measured Torque', 'Model Prediction');
    title(sprintf('Segment %d Fit: k = %.2f Nm/rad, b = %.4f Nms/rad (R^2 = %.1f%%)', ...
        s, k_est, b_est, R2));
        
    subplot(2,1,2);
    plot(seg_time, theta_flt, 'k', 'LineWidth', 1.5);
    grid on;
    xlabel('Time [s]');
    ylabel('Angle [rad]');
    drawnow;
end
%find fmax

%% =============================================================
%                   PRINT SUMMARY RESULTS
% =============================================================
Segment_ID   = (1:num_total_segments)';
SummaryTable = table(Segment_ID, k_est_all, b_est_all, r2_all, ...
    'VariableNames', {'Segment', 'Stiffness_k_Nm_rad', 'Damping_b_Nms_rad', 'R2_Fit_Percent'});

disp('========================================================================');
disp('          PHYSICALLY BOUNDED (NON-NEGATIVE) ESTIMATION RESULTS          ');
disp('========================================================================');
disp(SummaryTable);

% Overall Averages
fprintf('\n--- OVERALL AVERAGES ACROSS %d SEGMENTS ---\n', num_total_segments);
fprintf('Average Stiffness (k): %.4f N*m/rad\n', mean(k_est_all));
fprintf('Average Damping (b)  : %.6f N*m*s/rad\n', mean(b_est_all));
fprintf('Average Model Fit R^2: %.2f%%\n', mean(r2_all));

for s = 1:num_total_segments
    % Extract current segment
    idx         = start_indices(s):end_indices(s);
    seg_angle   = exp_sorted(idx, 1); 
    seg_load    = exp_sorted(idx, 2); 
    seg_time    = exp_sorted(idx, 3); 
    
    Ts = mean(diff(seg_time));
    Fs = 1/Ts; % Sampling Frequency [Hz]
    
    % Zero-mean signals
    raw_tau   = detrend(seg_load(:));
    raw_theta = detrend(deg2rad(seg_angle(:)));
    
    tau = raw_tau - mean(raw_tau);
    theta = raw_theta - mean(raw_theta);
    
    % Check sign convention
    corr_val = corr(tau, theta);
    if corr_val < 0
        theta = -theta;
    end
    
    % ----------------------------------------------------------
    % FIND MAX FREQUENCY (f_max) USING FFT FOR THIS SEGMENT
    % ----------------------------------------------------------
    N = length(tau);
    Y = fft(tau);
    f_vec = (0:N-1)*(Fs/N);
    power_spec = abs(Y).^2 / N;
    
    % Look at positive frequencies up to Nyquist limit (Fs/2)
    half_idx = 1:floor(N/2);
    pos_freqs = f_vec(half_idx);
    pos_power = power_spec(half_idx);
    
    % Find highest frequency component before power drops to noise floor
    % (Threshold: e.g., 1% of the peak power content)
    noise_threshold = max(pos_power) * 0.01;
    active_freqs = pos_freqs(pos_power > noise_threshold);
    f_max = max(active_freqs);
    
    fprintf('Segment %d: Estimated f_max = %.2f Hz\n', s, f_max);
    
    % ----------------------------------------------------------
    % ADAPTIVE LOW-PASS FILTER (e.g., set fc slightly above f_max)
    % ----------------------------------------------------------
    % Ensure fc doesn't exceed Nyquist and stays practical
    fc = min(f_max * 1.5, Fs / 2.1); 
    
    [b_flt, a_flt] = butter(2, fc / (Fs / 2), 'low');
    
    tau_flt   = filtfilt(b_flt, a_flt, tau);
    theta_flt = filtfilt(b_flt, a_flt, theta);
    
    % Compute velocity (theta_dot)
    dtheta = gradient(theta_flt) / Ts;
    
    % Rest of your least squares code...
    X_reg = [theta_flt, dtheta];
    params = lsqnonneg(X_reg, tau_flt);
    
    k_est = params(1); 
    b_est = params(2); 
    
    tau_pred = X_reg * params;
    SS_res = sum((tau_flt - tau_pred).^2);
    SS_tot = sum((tau_flt - mean(tau_flt)).^2);
    R2 = (1 - (SS_res / SS_tot)) * 100;
    
    k_est_all(s) = k_est;
    b_est_all(s) = b_est;
    r2_all(s)    = R2;
end
