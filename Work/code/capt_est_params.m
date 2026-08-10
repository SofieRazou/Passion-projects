clear
close all
clc

%% =============================================================
%                  KNOWN PHYSICAL PARAMETERS
% =============================================================
J = 0.0103; % Motor inertia [kg*m^2]
b = 1;      % Initial damping guess
k = 1;      % Initial stiffness guess

%% =============================================================
%                   LOAD AND EXTRACT DATA
% =============================================================
load('exp_sorted.mat'); % Fetches [angle, torque, time] matrix

% Correct column extractions:
seg_angle = exp_sorted(:, 1); % Column 1: Angle (deg)
seg_load  = exp_sorted(:, 2); % Column 2: Measured Torque (Nm)
seg_time  = exp_sorted(:, 3); % Column 3: Time (s) [FIXED TYPO HERE]

%% =============================================================
%                 PREPARE IDDATA FOR ANALYSIS
% =============================================================
% Calculate sampling time
Ts = mean(diff(seg_time));

% Zero-mean signals and convert angle to radians for physical modeling
u = seg_load(:) - mean(seg_load(:));
y = deg2rad(seg_angle(:) - mean(seg_angle(:)));

% Create System Identification Data Object
data_id = iddata(y, u, Ts);
data_id.InputName  = {'Measured torque'};
data_id.OutputName = {'Encoder angle'};
data_id.InputUnit  = {'Nm'};
data_id.OutputUnit = {'rad'};
data_id.ExperimentName = {'Exp_Sorted_Segment'};

%% =============================================================
%           1st ID METHOD: TRANSFER FUNCTION ESTIMATION
% =============================================================
% Estimates 2 poles, 0 zeros transfer function
Gest = tfest(data_id, 2, 0, NaN);

disp('Estimated Transfer Function (Gest):');
disp(Gest);

%% =============================================================
%            2nd ID METHOD: STATE-SPACE ESTIMATION
% =============================================================
% Fits a 2-state representation (position and velocity)
Gss = ssest(data_id, 2); 
Gss_tf = tf(Gss);

disp('Estimated State-Space Transfer Function (Gss_tf):');
disp(Gss_tf);

%% =============================================================
%                     BENCHMARKING & FIT
% =============================================================
[~, fit_tf] = compare(data_id, Gest);
[~, fit_ss] = compare(data_id, Gss);

fprintf('Transfer Function Fit: %.2f%%\n', fit_tf);
fprintf('State-Space Fit:       %.2f%%\n', fit_ss);

figure()
compare(data_id, Gest, Gss);
grid on
title('TF vs State-Space Comparison')
set(findall(gcf, 'Type', 'Line'), 'LineWidth', 2)
