clear
close all
clc

%% =============================================================
%                  KNOWN PHYSICAL PARAMETERS
% =============================================================
J_known = 0.0103; % Motor inertia [kg*m^2] (Fixed Auxiliary Parameter)

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
fit_gb_all = zeros(num_total_segments, 1);

%% =============================================================
%              LOOP THROUGH EACH EXPERIMENT SEGMENT
% =============================================================
for s = 1:num_total_segments
    % Extract current segment
    idx       = start_indices(s):end_indices(s);
    seg_angle = exp_sorted(idx, 1); % Column 1: Angle (deg)
    seg_load  = exp_sorted(idx, 2); % Column 2: Measured Torque (Nm)
    seg_time  = exp_sorted(idx, 3); % Column 3: Time (s)
    
    % Compute sampling time
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
    % GREY-BOX ESTIMATION (Direct Physical Parameter Fitting)
    % ----------------------------------------------------------
    p_init = [0.1; 1.0]; % Initial guesses: [b_guess; k_guess]
    
    % Construct idgrey model structure
    init_sys = idgrey(@motor_ode, p_init, 'c', J_known);
    
    % FIX: Capital 'P' in Parameters to prevent subasgn error
    init_sys.Structure.Parameters(1).Minimum = 0; % b_min >= 0
    init_sys.Structure.Parameters(2).Minimum = 0; % k_min >= 0
    
    % Estimate physical parameters using greyest
    opt = greyestOptions('Display', 'off');
    opt.SearchMethod = 'lm'; % Levenberg-Marquardt optimizer
    
    G_grey = greyest(data_id, init_sys, opt);
    
    % Extract estimated parameters cleanly using getpvec
    p_est = getpvec(G_grey);
    b_est = p_est(1);
    k_est = p_est(2);
    
    % Calculate model fit percentage
    [~, fit_gb] = compare(data_id, G_grey);
    
    % Store metrics
    b_est_all(s)  = b_est;
    k_est_all(s)  = k_est;
    fit_gb_all(s) = fit_gb;
    
    % Plot response for current segment
    figure('Name', sprintf('Segment %d Grey-Box Fit', s));
    compare(data_id, G_grey);
    grid on;
    title(sprintf('Segment %d Grey-Box Fit = %.1f%% (b = %.4f, k = %.4f)', ...
        s, fit_gb, b_est, k_est));
    set(findall(gcf, 'Type', 'Line'), 'LineWidth', 1.5);
    drawnow;
end

%% =============================================================
%                   PRINT SUMMARY RESULTS
% =============================================================
Segment_ID   = (1:num_total_segments)';
SummaryTable = table(Segment_ID, b_est_all, k_est_all, fit_gb_all, ...
    'VariableNames', {'Segment', 'Damping_b_Nms_rad', 'Stiffness_k_Nm_rad', 'GreyBox_Fit_Percent'});

disp('========================================================================');
disp('                  GREY-BOX SYSTEM IDENTIFICATION RESULTS                ');
disp('========================================================================');
disp(SummaryTable);

% Overall Averages
fprintf('\n--- OVERALL AVERAGES ACROSS %d SEGMENTS ---\n', num_total_segments);
fprintf('Average Damping (b)  : %.6f N*m*s/rad\n', mean(b_est_all));
fprintf('Average Stiffness (k): %.6f N*m/rad\n', mean(k_est_all));
fprintf('Average Model Fit    : %.2f%%\n', mean(fit_gb_all));

%% =============================================================
%             GREY-BOX LOCAL ODE MATRIX FUNCTION
% =============================================================
function [A, B, C, D, K, X0] = motor_ode(p, Ts, aux)
    % p(1) = b (damping)
    % p(2) = k (stiffness)
    % aux  = J (inertia)
    
    b = double(p(1));
    k = double(p(2));
    J = double(aux);
    
    A = [ 0   ,   1   ;
         -k/J ,  -b/J ];
     
    B = [ 0   ;
         1/J ];
     
    C = [ 1   ,   0  ];
    
    D = 0;
    
    K  = zeros(2, 1);
    X0 = zeros(2, 1);
end
