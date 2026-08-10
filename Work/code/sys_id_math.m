clear
close all
clc


%% =============================================================
%                       LOAD DATA
% =============================================================

load('exp_distance.mat')

id = ['100';'116';'098';'097';'095';'090';'085';'093';'092'];

num_experiments = length(id);


%% =============================================================
%              INITIALIZE IDENTIFICATION STORAGE
% =============================================================

results = struct();

% Individual identified models
Gest_all  = {};
Gss_all   = {};
Ggrey_all = {};

% Models that will actually be merged
TF_models_for_merge   = {};
SS_models_for_merge   = {};
Grey_models_for_merge = {};

% Identification data sets
IDdata_all = {};

% Fit values
fit_tf_all   = [];
fit_ss_all   = [];
fit_grey_all = [];


%% =============================================================
%               LOOP THROUGH EXPERIMENTS
% =============================================================

for i = 1:num_experiments

    experiment_id = id(i,:);

    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change=t_change',experiment_id,';'))


    %% =========================================================
    %                  BASIC SIGNAL EXTRACTION
    % =========================================================

    time = data(:,1);

    % Encoder position
    angle = data(:,4);       % degrees

    % Default:
    % [force, torque_sent, iA_sent, iB_sent]
    c_idx = [5 7 9 8];


    %% =========================================================
    %                  CHANNEL / GAIN SELECTION
    % ==========================================================

    experiment_number = str2double(experiment_id);

    if experiment_number < 92

        g = 1;

    elseif experiment_number < 100

        c_idx = [6 8 10 9];
        g = 4;

    elseif experiment_number < 110

        g = 4;

    else

        g = 1;

        % Remove encoder offset
        angle = angle - 58.1;

    end


    %% =========================================================
    %                  EXTRACT RAW SIGNALS
    % ==========================================================

    force = data(:,c_idx(1));

    % Commanded torque
    torque_sent = -data(:,c_idx(2))*g;

    % Sent motor currents
    iA_sent = data(:,c_idx(3));
    iB_sent = data(:,c_idx(4));


    %% =========================================================
    %                  FILTERING
    % ==========================================================

    fs = 1/mean(diff(time));

    fc = 20;

    [b_filt,a_filt] = butter(8,fc/(fs/2),'low');


    %% =========================================================
    %              LOAD CELL FORCE -> TORQUE
    % ==========================================================

    torque_load = force*0.0846;

    filtered_torque_load = filtfilt(...
        b_filt,a_filt,...
        torque_load);


    %% =========================================================
    %                    PRELOAD
    % ==========================================================

    torque_preload = mean(torque_sent);

    load_preload = mean(filtered_torque_load);

    center(i) = mean(angle);


    %% =========================================================
    %              FIGURE 1: COMPLETE EXPERIMENT
    % ==========================================================

    figure()

    subplot(3,1,1)

    plot(...
        time,...
        torque_sent,...
        'Color',[.4 .4 .4],...
        'LineWidth',1)

    hold on

    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    ylabel("Commanded torque (Nm)")
    title(['Experiment ',experiment_id])


    subplot(3,1,2)

    plot(...
        time,...
        angle,...
        'LineWidth',1)

    hold on

    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    ylabel("Angle (deg)")


    subplot(3,1,3)

    plot(...
        time,...
        filtered_torque_load-load_preload+torque_preload,...
        'Color',[.8 .3 .2],...
        'LineWidth',1)

    hold on

    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    xlabel("Time (s)")
    ylabel("Measured torque (Nm)")


    %% =========================================================
    %                  FIND SEGMENT INDICES
    % ==========================================================

    event_idx = zeros(size(t_change));

    for k = 1:length(t_change)

        [~,event_idx(k)] = ...
            min(abs(time-t_change(k)));

    end

    num_segments = length(event_idx)-1;


    %% =========================================================
    %           INITIALIZE RESULTS FOR THIS EXPERIMENT
    % ==========================================================

    results(i).experiment_id = experiment_id;
    results(i).fs = fs;
    results(i).filter_cutoff = fc;
    results(i).gain = g;
    results(i).center_deg = center(i);
    results(i).num_segments = num_segments;

    results(i).segment = struct();


    %% =========================================================
    %              FIGURE 2: TORQUE TRACKING
    % ==========================================================

    figure()


    %% =========================================================
    %                  LOOP THROUGH SEGMENTS
    % ==========================================================

    for seg = 1:num_segments


        %% -----------------------------------------------------
        % Extract original segment
        % ------------------------------------------------------

        i_start0 = event_idx(seg);
        i_end0   = event_idx(seg+1);

        seg_t = time(i_start0:i_end0);

        seg_torque_sent = ...
            torque_sent(i_start0:i_end0) ...
            - torque_preload;


        %% -----------------------------------------------------
        % Extract 5 complete torque periods
        % ------------------------------------------------------

        [seg_sent,...
         seg_time,...
         i_start,...
         i_end] = ...
            extract_5_periods(...
            seg_t,...
            seg_torque_sent);


        %% -----------------------------------------------------
        % Extract measured physical torque
        % ------------------------------------------------------

        seg_load = ...
            filtered_torque_load(...
            i_start0+i_start : ...
            i_start0+i_end) ...
            - load_preload;


        %% -----------------------------------------------------
        % Extract encoder angle
        % ------------------------------------------------------

        seg_angle_deg = ...
            angle(...
            i_start0+i_start : ...
            i_start0+i_end);


        %% -----------------------------------------------------
        % Convert angle degrees -> radians
        % ------------------------------------------------------

        seg_angle = deg2rad(seg_angle_deg);


        %% -----------------------------------------------------
        % Remove equilibrium position
        % ------------------------------------------------------

        seg_angle = ...
            seg_angle - mean(seg_angle);


        %% =====================================================
        %                   ANGLE ANALYSIS
        % ======================================================

        c_angle(i,seg) = mean(seg_angle_deg);

        [pks_max,~] = findpeaks(seg_angle_deg);
        [pks_min,~] = findpeaks(-seg_angle_deg);
        pks_min = -pks_min;

        if length(pks_max) >= 5 && length(pks_min) >= 5
            pks_max = maxk(pks_max,5);
            pks_min = mink(pks_min,5);

            d_angle(i,seg) = mean(pks_max)-mean(pks_min);
        else
            d_angle(i,seg) = NaN;
        end


        %% =====================================================
        %                   TORQUE TRACKING
        % ======================================================

        dTorque(i,seg) = max(seg_sent)-min(seg_sent);


        %% =====================================================
        %                   CORRELATION
        % ======================================================

        [R,P] = corrcoef(seg_sent, seg_load);

        r(i,seg) = R(1,2);
        p(i,seg) = P(1,2);


        %% =====================================================
        %                     MAE
        % ======================================================

        rm(i,seg) = mean(abs(seg_sent-seg_load));

        rm_perc(i,seg) = rm(i,seg) / (max(seg_sent)-min(seg_sent));


        %% =====================================================
        %                     R-SQUARED
        % ======================================================

        SS_res = sum((seg_sent-seg_load).^2);
        SS_tot = sum((seg_sent-mean(seg_load)).^2);

        R2(i,seg) = 1-SS_res/SS_tot;


        %% =====================================================
        %                 PLATEAU / EDGE ANALYSIS
        % ======================================================

        dx = gradient(seg_sent);
        thr = 0.05*max(abs(dx(5:end)));

        is_plateau = abs(dx) < thr;
        is_edge = ~is_plateau;

        gain_plateau(i,seg) = sum(seg_load(is_plateau).*seg_sent(is_plateau)) / sum(seg_sent(is_plateau).^2);
        rmse_plateau(i,seg) = sqrt(mean((seg_load(is_plateau)-seg_sent(is_plateau)).^2));
        rmse_edge(i,seg)    = sqrt(mean((seg_sent(is_edge)-seg_load(is_edge)).^2));


        %% =====================================================
        %             PLOT TORQUE TRACKING
        % ======================================================

        subplot(num_segments,1,seg)

        plot(...
            seg_time-seg_time(1),...
            seg_sent+torque_preload,...
            'Color',[.4 .4 .4],...
            'LineWidth',1)

        hold on

        plot(...
            seg_time-seg_time(1),...
            seg_load+torque_preload,...
            'Color',[.8 .3 .2],...
            'LineWidth',1)

        ylabel("Torque (Nm)")

        xlim([0, seg_time(end)-seg_time(1)])

        if seg == num_segments
            xlabel("Time (s)")
        end

        if seg == 1
            legend('Commanded torque','Measured torque','Location','best')
        end


        %% =====================================================
        %                  PREPARE ID DATA
        % ======================================================

        Ts = mean(diff(seg_time));

        u = seg_load(:);
        y = seg_angle(:);

        % Remove DC component from input
        u = u - mean(u);

        % Create identification data
        data_id = iddata(y, u, Ts);

        data_id.InputName = {'Measured torque'};
        data_id.OutputName = {'Encoder angle'};
        data_id.InputUnit = {'Nm'};
        data_id.OutputUnit = {'rad'};
        data_id.ExperimentName = {['Exp',experiment_id,'_Seg',num2str(seg)]};


        %% =====================================================
        %           IDENTIFICATION METHOD 1: TRANSFER FUNCTION
        % ======================================================

        Gest = tfest(data_id, 2, 0, NaN);


        %% =====================================================
        %           IDENTIFICATION METHOD 2: STATE SPACE
        % ======================================================

        Gss = ssest(data_id, 2);
        Gss_tf = tf(Gss);


        %% =====================================================
        %           IDENTIFICATION METHOD 3: GREY-BOX (idgrey)
        % ======================================================

        J_known = 0.0103;  % Known Inertia [kg*m^2]
        k_init  = 100.0;   % Initial guess for stiffness
        b_init  = 0.1;     % Initial guess for damping

        % Setup idgrey structure using ODE function motor_ode
        init_sys = idgrey('motor_ode', {k_init, b_init}, 'c', {J_known});
        
        % Ensure parameters stay non-negative
        init_sys.Structure.Parameters(1).Minimum = 0; % k >= 0
        init_sys.Structure.Parameters(2).Minimum = 0; % b >= 0

        % Perform Grey-Box Optimization
        opt = greyestOptions('Display','off');
        Ggrey = greyest(data_id, init_sys, opt);

        % Extract parameters
        p_est = Ggrey.Report.Parameters.ParVector;
        k_grey = p_est(1);
        b_grey = p_est(2);


        %% =====================================================
        %                  MODEL FITS
        % ======================================================

        [~,fit_tf]   = compare(data_id, Gest);
        [~,fit_ss]   = compare(data_id, Gss);
        [~,fit_grey] = compare(data_id, Ggrey);


        %% =====================================================
        %                 EXTRACT TF PARAMETERS
        % ======================================================

        [num_tf,den_tf] = tfdata(Gest,'v');
        num_tf = num_tf(:).';
        den_tf = den_tf(:).';

        if length(den_tf) == 3
            a1 = den_tf(2);
            a0 = den_tf(3);
            wn_tf = sqrt(abs(a0));
            zeta_tf = (wn_tf > 0) * (a1/(2*wn_tf));
        else
            a1 = NaN; a0 = NaN; wn_tf = NaN; zeta_tf = NaN;
        end

        poles_tf = pole(Gest);

        b_tf = J_known * a1;
        k_tf = J_known * a0;


        %% =====================================================
        %                 EXTRACT SS PARAMETERS
        % ======================================================

        A = Gss.A; B = Gss.B; C = Gss.C; D = Gss.D;
        poles_ss = pole(Gss);

        if length(poles_ss) == 2
            wn_ss = sqrt(abs(poles_ss(1)*poles_ss(2)));
            zeta_ss = (wn_ss > 0) * (-real(sum(poles_ss))/(2*wn_ss));
        else
            wn_ss = NaN; zeta_ss = NaN;
        end


        %% =====================================================
        %                 STORE RESULTS
        % ======================================================

        results(i).segment(seg).segment_number = seg;
        results(i).segment(seg).Ts = Ts;
        results(i).segment(seg).center_deg = c_angle(i,seg);
        results(i).segment(seg).torque_amplitude = dTorque(i,seg);
        results(i).segment(seg).angle_amplitude_deg = d_angle(i,seg);

        % Tracking
        results(i).segment(seg).tracking.correlation = r(i,seg);
        results(i).segment(seg).tracking.p_value = p(i,seg);
        results(i).segment(seg).tracking.MAE = rm(i,seg);
        results(i).segment(seg).tracking.MAE_percent = rm_perc(i,seg);
        results(i).segment(seg).tracking.R2 = R2(i,seg);
        results(i).segment(seg).tracking.plateau_gain = gain_plateau(i,seg);
        results(i).segment(seg).tracking.plateau_RMSE = rmse_plateau(i,seg);
        results(i).segment(seg).tracking.edge_RMSE = rmse_edge(i,seg);

        % Identification Data
        results(i).segment(seg).identification.data = data_id;
        results(i).segment(seg).identification.input = u;
        results(i).segment(seg).identification.output = y;

        % Transfer Function
        results(i).segment(seg).TF.model = Gest;
        results(i).segment(seg).TF.numerator = num_tf;
        results(i).segment(seg).TF.denominator = den_tf;
        results(i).segment(seg).TF.poles = poles_tf;
        results(i).segment(seg).TF.fit_percent = fit_tf;
        results(i).segment(seg).TF.wn = wn_tf;
        results(i).segment(seg).TF.zeta = zeta_tf;
        results(i).segment(seg).TF.a1 = a1;
        results(i).segment(seg).TF.a0 = a0;
        results(i).segment(seg).TF.b = b_tf;
        results(i).segment(seg).TF.k = k_tf;

        % State Space
        results(i).segment(seg).SS.model = Gss;
        results(i).segment(seg).SS.A = A;
        results(i).segment(seg).SS.B = B;
        results(i).segment(seg).SS.C = C;
        results(i).segment(seg).SS.D = D;
        results(i).segment(seg).SS.poles = poles_ss;
        results(i).segment(seg).SS.fit_percent = fit_ss;
        results(i).segment(seg).SS.wn = wn_ss;
        results(i).segment(seg).SS.zeta = zeta_ss;
        results(i).segment(seg).SS.transfer_function = Gss_tf;

        % Grey-Box (idgrey)
        results(i).segment(seg).Grey.model = Ggrey;
        results(i).segment(seg).Grey.k = k_grey;
        results(i).segment(seg).Grey.b = b_grey;
        results(i).segment(seg).Grey.J = J_known;
        results(i).segment(seg).Grey.fit_percent = fit_grey;


        %% =====================================================
        %          STORE MODELS FOR LATER MERGING
        % ======================================================

        Gest_all{i,seg}  = Gest;
        Gss_all{i,seg}   = Gss;
        Ggrey_all{i,seg} = Ggrey;

        fit_tf_all(i,seg)   = fit_tf;
        fit_ss_all(i,seg)   = fit_ss;
        fit_grey_all(i,seg) = fit_grey;

        IDdata_all{i,seg} = data_id;

        TF_models_for_merge{end+1}   = Gest;
        SS_models_for_merge{end+1}   = Gss;
        Grey_models_for_merge{end+1} = Ggrey;


        %% =====================================================
        %             MODEL COMPARISON FIGURE
        % ======================================================

        figure()
        compare(data_id, Gest, Gss, Ggrey);
        grid on
        title(['TF vs SS vs Grey-Box - Exp ', experiment_id, ', Seg ', num2str(seg)])
        set(findall(gcf,'Type','Line'),'LineWidth',2)


        %% =====================================================
        %                DISPLAY RESULTS
        % ======================================================

        disp(' ')
        disp('======================================================')
        disp(['Experiment: ',experiment_id, ' | Segment: ',num2str(seg)])
        disp('======================================================')
        disp(['TF Fit:   ', num2str(fit_tf),   ' %'])
        disp(['SS Fit:   ', num2str(fit_ss),   ' %'])
        disp(['Grey Fit: ', num2str(fit_grey), ' %'])
        disp(['Estimated Stiffness (k): ', num2str(k_grey), ' Nm/rad'])
        disp(['Estimated Damping (b):   ', num2str(b_grey), ' Nm*s/rad'])

    end

end


%% =============================================================
%              MERGE ALL TRANSFER FUNCTION MODELS
% =============================================================

disp(' ')
disp('======================================================')
disp('             MERGING TRANSFER FUNCTION MODELS')
disp('======================================================')

if ~isempty(TF_models_for_merge)
    GTF_merged = merge(TF_models_for_merge{:});
    results_merged.TF.model = GTF_merged;
    [num_merged,den_merged] = tfdata(GTF_merged,'v');
    results_merged.TF.numerator = num_merged;
    results_merged.TF.denominator = den_merged;
    results_merged.TF.poles = pole(GTF_merged);
end


%% =============================================================
%              MERGE ALL STATE-SPACE MODELS
% =============================================================

disp(' ')
disp('======================================================')
disp('              MERGING STATE-SPACE MODELS')
disp('======================================================')

if ~isempty(SS_models_for_merge)
    GSS_merged = merge(SS_models_for_merge{:});
    results_merged.SS.model = GSS_merged;
    results_merged.SS.A = GSS_merged.A;
    results_merged.SS.B = GSS_merged.B;
    results_merged.SS.C = GSS_merged.C;
    results_merged.SS.D = GSS_merged.D;
    results_merged.SS.poles = pole(GSS_merged);
end


%% =============================================================
%              MERGE ALL GREY-BOX MODELS
% =============================================================

disp(' ')
disp('======================================================')
disp('               MERGING GREY-BOX MODELS')
disp('======================================================')

if ~isempty(Grey_models_for_merge)
    GGrey_merged = merge(Grey_models_for_merge{:});
    results_merged.Grey.model = GGrey_merged;
    
    p_merged = GGrey_merged.Report.Parameters.ParVector;
    results_merged.Grey.k = p_merged(1);
    results_merged.Grey.b = p_merged(2);
    results_merged.Grey.J = J_known;

    disp(['Unified Merged Stiffness (k): ', num2str(p_merged(1)), ' Nm/rad'])
    disp(['Unified Merged Damping (b):   ', num2str(p_merged(2)), ' Nm*s/rad'])
end


%% =============================================================
%                  SUMMARY TABLE
% =============================================================

summary_rows = [];

for i = 1:num_experiments
    for seg = 1:results(i).num_segments
        row.experiment = string(id(i,:));
        row.segment = seg;
        row.TF_fit = results(i).segment(seg).TF.fit_percent;
        row.SS_fit = results(i).segment(seg).SS.fit_percent;
        row.Grey_fit = results(i).segment(seg).Grey.fit_percent;
        row.Grey_k = results(i).segment(seg).Grey.k;
        row.Grey_b = results(i).segment(seg).Grey.b;
        
        summary_rows = [summary_rows; row];
    end
end


%% =============================================================
%                  SAVE EVERYTHING
% =============================================================

save('system_identification_results.mat',...
    'results',...
    'results_merged',...
    'Gest_all',...
    'Gss_all',...
    'Ggrey_all',...
    'fit_tf_all',...
    'fit_ss_all',...
    'fit_grey_all',...
    'IDdata_all',...
    'center',...
    'c_angle',...
    'd_angle',...
    'dTorque',...
    'r',...
    'p',...
    'rm',...
    'rm_perc',...
    'R2',...
    'gain_plateau',...
    'rmse_plateau',...
    'rmse_edge')

disp(' ')
disp('======================================================')
disp('           SYSTEM IDENTIFICATION COMPLETE')
disp('======================================================')


%% =============================================================
%         FUNCTION: MOTOR ODE FOR GREY-BOX IDENTIFICATION
% =============================================================

function [A, B, C, D] = motor_ode(k, b, Ts, Jm)
    % A matrix
    A = [0,         1;
        -k/Jm,  -b/Jm];
    
    % B matrix
    B = [0;
         1/Jm];
    
    % C matrix (Measuring Encoder Angle theta)
    C = [1, 0];
    
    % D matrix
    D = 0;
end


%% =============================================================
%               FUNCTION: EXTRACT 5 PERIODS
% =============================================================

function [segment,...
          t_segment,...
          idx_start,...
          idx_end] = ...
          extract_5_periods(t,signal)

% Normalize signal
signal_range = max(signal)-min(signal);

if signal_range == 0
    error('Signal has zero amplitude.')
end

sig_norm = (signal-min(signal)) / signal_range;

% Sampling time
dt = mean(diff(t));

% Derivative
dsig = diff(sig_norm)/dt;

% Find approximate indices for 5 complete periods
% (Using zero crossings / peak thresholds)
[~, locs] = findpeaks(sig_norm, 'MinPeakDistance', round(0.5/dt));

if length(locs) >= 6
    idx_start = locs(1);
    idx_end   = locs(6);
else
    idx_start = 1;
    idx_end   = length(signal);
end

segment   = signal(idx_start:idx_end);
t_segment = t(idx_start:idx_end);

end




%"Real" physical system dynamics
s = tf('s');
Greal = 5*(s+1)/(s^2 + 6*s + 6.7)*exp(-0.1*s);
Ts = 0.01; %sample time in sec
%Data collection with said input and output tracking
dt = Ts;
t = 0:dt:5;

u = ones(length(t),1);
u(1:1/dt) = 0; %inital condition

yreal = lsim(Greal, u, t);

plot(t, [u, yreal], 'LineWidth', 4);
axis([0 5 0 1.4]);
grid on;
legend(['u';'y']);

%Fit data to said model structure 
data = iddata(yreal, u, dt);
Gest = tfest(data,2, 0, NaN);

%Draw comparison between the dynamics and the fitted model 
opt = compareOptions;
opt.InitialCondition = 'z';
compare(data,Gest,opt);
set(findall(gca, 'Type', 'Line'), 'LineWidth', 4');
grid on;
