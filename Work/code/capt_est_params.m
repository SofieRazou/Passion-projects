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
fprintf('Average Model Fit    : %.2f%%\n', mean(fit_tf_all));
