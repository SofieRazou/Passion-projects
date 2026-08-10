clear
close all
clc

%% =============================================================
%                  KNOWN PHYSICAL PARAMETERS
% =============================================================
J = 0.0103; % Motor inertia [kg*m^2]

%% =============================================================
%                   LOAD AND EXTRACT DATA
% =============================================================
% Load data and parameters saved by the first script
load('exp_sorted.mat'); 

seg_angle = exp_sorted(:, 1); % Column 1: Angle (deg)
seg_load  = exp_sorted(:, 2); % Column 2: Measured Torque (Nm)
raw_time  = exp_sorted(:, 3); % Column 3: Time (s)

% --- FIX: Handle non-monotonic time vector due to concatenated segments ---
% Find positive time steps to compute real sampling rate Ts
dt_vec = diff(raw_time);
valid_dt = dt_vec(dt_vec > 0); 
Ts = mean(valid_dt);

% Reconstruct continuous time vector for plotting/iddata consistency
seg_time = (0:length(seg_angle)-1)' * Ts;

%% =============================================================
%                 PREPARE IDDATA FOR ANALYSIS
% =============================================================
% Zero-mean signals and convert angle to radians for physical modeling
u = seg_load(:) - mean(seg_load(:));
y = deg2rad(seg_angle(:) - mean(seg_angle(:)));

% Safely fetch experiment name metadata if saved, else default
if ~exist('experiment_id', 'var'), experiment_id = 'Sorted'; end
if ~exist('seg', 'var'), seg = 1; end

% Create System Identification Data Object
data_id = iddata(y, u, Ts);
data_id.InputName  = {'Measured torque'};
data_id.OutputName = {'Encoder angle'};
data_id.InputUnit  = {'Nm'};
data_id.OutputUnit = {'rad'};
data_id.ExperimentName = {['Exp_', num2str(experiment_id), '_Seg_', num2str(seg)]};

%% =============================================================
%           1st ID METHOD: TRANSFER FUNCTION ESTIMATION
% =============================================================
% Fits 2 poles and 0 zeros: G(s) = K / (s^2 + a1*s + a0)
Gest = tfest(data_id, 2, 0, NaN);

disp('--------------------------------------------------');
disp('Estimated Transfer Function (Gest):');
disp(Gest);

% Extract physical parameters (b and k) from Gest
[num, den] = tfdata(Gest, 'v');
gain_scale = (1/J) / num(end);
b_est = den(2) * gain_scale * J;
k_est = den(3) * gain_scale * J;

fprintf('Extracted Physical Damping (b):   %.4f N*m*s/rad\n', b_est);
fprintf('Extracted Physical Stiffness (k): %.4f N*m/rad\n', k_est);
disp('--------------------------------------------------');

%% =============================================================
%            2nd ID METHOD: STATE-SPACE ESTIMATION
% =============================================================
% Fits 2-state model (position and velocity)
Gss = ssest(data_id, 2); 
Gss_tf = tf(Gss);

disp('Estimated State-Space Model (Converted to TF):');
disp(Gss_tf);

%% =============================================================
%                     BENCHMARKING & FIT
% =============================================================
[~, fit_tf] = compare(data_id, Gest);
[~, fit_ss] = compare(data_id, Gss);

fprintf('Transfer Function Model Fit: %.2f%%\n', fit_tf);
fprintf('State-Space Model Fit:       %.2f%%\n', fit_ss);

figure()
compare(data_id, Gest, Gss);
grid on
title(sprintf('TF vs State-Space Comparison (Exp: %s, Seg: %d)', num2str(experiment_id), seg));
set(findall(gcf, 'Type', 'Line'), 'LineWidth', 2);
