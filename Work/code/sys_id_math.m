clear
close all
clc

J = 0.0103; %known inertia of the CAPT Motor in kg*m^2
b= 1;
k = 1; %dummy val placeholders for later on grey-box estimation 
%% =============================================================
%                      LOAD DATA
% =============================================================

load('exp_distance.mat')

id = ['100';'116';'098';'097';'095';'090';'085';'093';'092'];

num_experiments = length(id);


%% =============================================================
%              INITIALIZE IDENTIFICATION STORAGE
% =============================================================

results = struct();

% Individual identified models
Gest_all = {};
Gss_all  = {};

% Models that will actually be merged
TF_models_for_merge = {};
SS_models_for_merge = {};

% Identification data sets
IDdata_all = {};

% Fit values
fit_tf_all = [];
fit_ss_all = [];


%% =============================================================
%                  LOOP THROUGH EXPERIMENTS
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

    [b,a] = butter(8,fc/(fs/2),'low');


    %% =========================================================
    %              LOAD CELL FORCE -> TORQUE
    % ==========================================================

    torque_load = force*0.0846;

    filtered_torque_load = filtfilt(...
        b,a,...
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
        %
        % IDENTIFICATION INPUT
        % ------------------------------------------------------

        seg_load = ...
            filtered_torque_load(...
            i_start0+i_start : ...
            i_start0+i_end) ...
            - load_preload;


        %% -----------------------------------------------------
        % Extract encoder angle
        %
        % IDENTIFICATION OUTPUT
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
        %                  ANGLE ANALYSIS
        % ======================================================

        c_angle(i,seg) = mean(seg_angle_deg);


        [pks_max,~] = ...
            findpeaks(seg_angle_deg);

        [pks_min,~] = ...
            findpeaks(-seg_angle_deg);

        pks_min = -pks_min;


        if length(pks_max) >= 5 && ...
           length(pks_min) >= 5

            pks_max = maxk(pks_max,5);
            pks_min = mink(pks_min,5);

            d_angle(i,seg) = ...
                mean(pks_max)-mean(pks_min);

        else

            d_angle(i,seg) = NaN;

        end


        %% =====================================================
        %                  TORQUE TRACKING
        % ======================================================

        dTorque(i,seg) = ...
            max(seg_sent)-min(seg_sent);


        %% =====================================================
        %                  CORRELATION
        % ======================================================

        [R,P] = corrcoef(...
            seg_sent,...
            seg_load);

        r(i,seg) = R(1,2);
        p(i,seg) = P(1,2);


        %% =====================================================
        %                     MAE
        % ======================================================

        rm(i,seg) = ...
            mean(abs(...
            seg_sent-seg_load));

        rm_perc(i,seg) = ...
            rm(i,seg) / ...
            (max(seg_sent)-min(seg_sent));


        %% =====================================================
        %                     R-SQUARED
        % ======================================================

        SS_res = ...
            sum((seg_sent-seg_load).^2);

        SS_tot = ...
            sum((seg_sent-mean(seg_load)).^2);

        R2(i,seg) = ...
            1-SS_res/SS_tot;


        %% =====================================================
        %                PLATEAU / EDGE ANALYSIS
        % ======================================================

        dx = gradient(seg_sent);

        thr = ...
            0.05*max(abs(dx(5:end)));

        is_plateau = abs(dx) < thr;

        is_edge = ~is_plateau;


        % Plateau gain

        gain_plateau(i,seg) = ...
            sum(seg_load(is_plateau).* ...
                seg_sent(is_plateau)) / ...
            sum(seg_sent(is_plateau).^2);


        % Plateau RMSE

        rmse_plateau(i,seg) = ...
            sqrt(mean(...
            (seg_load(is_plateau)- ...
             seg_sent(is_plateau)).^2));


        % Edge RMSE

        rmse_edge(i,seg) = ...
            sqrt(mean(...
            (seg_sent(is_edge)- ...
             seg_load(is_edge)).^2));


        %% =====================================================
        %              PLOT TORQUE TRACKING
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

        xlim([...
            0,...
            seg_time(end)-seg_time(1)])


        if seg == num_segments

            xlabel("Time (s)")

        end


        if seg == 1

            legend(...
                'Commanded torque',...
                'Measured torque',...
                'Location','best')

        end


        %% =====================================================
        % ======================================================
        %
        %              SYSTEM IDENTIFICATION
        %
        % ======================================================
        %
        % INPUT:
        %     measured physical torque
        %
        %     u(t) = seg_load
        %
        % OUTPUT:
        %     encoder angle
        %
        %     y(t) = seg_angle
        %
        % Therefore:
        %
        %       Torque ---> CAPT motor ---> Angle
        %
        %       G(s) = Theta(s) / Torque(s)
        %
        % ======================================================


        %% =====================================================
        %                 PREPARE ID DATA
        % ======================================================

        Ts = mean(diff(seg_time));

        u = seg_load(:);
        y = seg_angle(:);


        % Remove DC component from input

        u = u - mean(u);


        % Create identification data

        data_id = iddata(...
            y,...
            u,...
            Ts);


        % Give the signals meaningful names

        data_id.InputName = {'Measured torque'};
        data_id.OutputName = {'Encoder angle'};

        data_id.InputUnit = {'Nm'};
        data_id.OutputUnit = {'rad'};

        data_id.ExperimentName = {...
            ['Exp',experiment_id,'_Seg',num2str(seg)]};


        %% =====================================================
        %          IDENTIFICATION METHOD 1:
        %               TRANSFER FUNCTION
        % ======================================================

        % Second-order transfer function

        Gest = tfest(...
            data_id,...
            2,...
            0,...
            NaN);


        %% =====================================================
        %          IDENTIFICATION METHOD 2:
        %                 STATE SPACE
        % ======================================================

        % Two-state state-space model

        Gss = ssest(...
            data_id,...
            1);


        % Convert SS model to TF

        Gss_tf = tf(Gss);


        %% =====================================================
        %                 MODEL FIT
        % ======================================================

        [~,fit_tf] = compare(...
            data_id,...
            Gest);

        [~,fit_ss] = compare(...
            data_id,...
            Gss);


        %% =====================================================
        %                 EXTRACT TF PARAMETERS
        % ======================================================

        [num_tf,den_tf] = ...
            tfdata(Gest,'v');

        num_tf = num_tf(:).';
        den_tf = den_tf(:).';


        % Make denominator second order if possible

        if length(den_tf) == 3

            a1 = den_tf(2);
            a0 = den_tf(3);

            wn_tf = sqrt(abs(a0));

            if wn_tf > 0

                zeta_tf = ...
                    a1/(2*wn_tf);

            else

                zeta_tf = NaN;

            end

        else

            a1 = NaN;
            a0 = NaN;
            wn_tf = NaN;
            zeta_tf = NaN;

        end


        poles_tf = pole(Gest);


        %% =====================================================
        %          PHYSICAL PARAMETERS FROM TF
        % ======================================================

        % Mechanical model:
        %
        % J*theta_ddot + b*theta_dot + k*theta = tau
        %
        % Therefore:
        %
        %        Theta(s)          1
        % G(s) = -------- = -----------------
        %        Tau(s)      J*s^2+b*s+k
        %
        % Normalized:
        %
        %              1/J
        % G(s) = -------------------
        %        s^2+(b/J)s+(k/J)
        %
        % Thus:
        %
        %       b/J = a1
        %       k/J = a0
        %
        % If J is known:
        %
        %       b = J*a1
        %       k = J*a0


        J_known = NaN;


        if ~isnan(J_known) && ...
           length(den_tf) == 3

            b_tf = J_known*a1;
            k_tf = J_known*a0;

        else

            b_tf = NaN;
            k_tf = NaN;

        end


        %% =====================================================
        %                 EXTRACT SS PARAMETERS
        % ======================================================

        A = Gss.A;
        B = Gss.B;
        C = Gss.C;
        D = Gss.D;

        poles_ss = pole(Gss);


        %% =====================================================
        %          SS NATURAL FREQUENCY / DAMPING
        % ======================================================

        if length(poles_ss) == 2

            wn_ss = sqrt(...
                abs(poles_ss(1)*poles_ss(2)));

            if wn_ss > 0

                zeta_ss = ...
                    -real(sum(poles_ss))/(2*wn_ss);

            else

                zeta_ss = NaN;

            end

        else

            wn_ss = NaN;
            zeta_ss = NaN;

        end


        %% =====================================================
        %                 STORE RESULTS
        % ======================================================

        results(i).segment(seg).segment_number = seg;

        results(i).segment(seg).Ts = Ts;

        results(i).segment(seg).center_deg = ...
            c_angle(i,seg);

        results(i).segment(seg).torque_amplitude = ...
            dTorque(i,seg);

        results(i).segment(seg).angle_amplitude_deg = ...
            d_angle(i,seg);


        %% -----------------------------------------------------
        % Torque tracking
        % ------------------------------------------------------

        results(i).segment(seg).tracking.correlation = ...
            r(i,seg);

        results(i).segment(seg).tracking.p_value = ...
            p(i,seg);

        results(i).segment(seg).tracking.MAE = ...
            rm(i,seg);

        results(i).segment(seg).tracking.MAE_percent = ...
            rm_perc(i,seg);

        results(i).segment(seg).tracking.R2 = ...
            R2(i,seg);

        results(i).segment(seg).tracking.plateau_gain = ...
            gain_plateau(i,seg);

        results(i).segment(seg).tracking.plateau_RMSE = ...
            rmse_plateau(i,seg);

        results(i).segment(seg).tracking.edge_RMSE = ...
            rmse_edge(i,seg);


        %% -----------------------------------------------------
        % Identification data
        % ------------------------------------------------------

        results(i).segment(seg).identification.data = ...
            data_id;

        results(i).segment(seg).identification.input = u;

        results(i).segment(seg).identification.output = y;


        %% -----------------------------------------------------
        % Transfer function
        % ------------------------------------------------------

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


        %% -----------------------------------------------------
        % State space
        % ------------------------------------------------------

        results(i).segment(seg).SS.model = Gss;

        results(i).segment(seg).SS.A = A;

        results(i).segment(seg).SS.B = B;

        results(i).segment(seg).SS.C = C;

        results(i).segment(seg).SS.D = D;

        results(i).segment(seg).SS.poles = poles_ss;

        results(i).segment(seg).SS.fit_percent = fit_ss;

        results(i).segment(seg).SS.wn = wn_ss;

        results(i).segment(seg).SS.zeta = zeta_ss;


        %% -----------------------------------------------------
        % SS -> TF
        % ------------------------------------------------------

        results(i).segment(seg).SS.transfer_function = Gss_tf;


        %% =====================================================
        %          STORE MODELS FOR LATER MERGING
        % ======================================================

        Gest_all{i,seg} = Gest;
        Gss_all{i,seg} = Gss;

        fit_tf_all(i,seg) = fit_tf;
        fit_ss_all(i,seg) = fit_ss;

        IDdata_all{i,seg} = data_id;


        % IMPORTANT:
        %
        % merge() requires models of the SAME structure.
        %
        % Therefore:
        %
        %   TF models are collected separately
        %   SS models are collected separately
        %
        % We do NOT merge TF and SS together.


        TF_models_for_merge{end+1} = Gest;

        SS_models_for_merge{end+1} = Gss;


        %% =====================================================
        %             MODEL COMPARISON FIGURE
        % ======================================================

        figure()

        compare(...
            data_id,...
            Gest,...
            Gss);

        grid on

        title([...
            'TF vs State-Space - Experiment ',...
            experiment_id,...
            ', Segment ',num2str(seg)])

        set(...
            findall(gcf,'Type','Line'),...
            'LineWidth',2)


        %% =====================================================
        %                 DISPLAY RESULTS
        % ======================================================

        disp(' ')
        disp('======================================================')
        disp(['Experiment: ',experiment_id])
        disp(['Segment:    ',num2str(seg)])
        disp('======================================================')


        disp(' ')
        disp('IDENTIFICATION DATA')
        disp('Input  = measured load-cell torque [Nm]')
        disp('Output = encoder angle [rad]')


        disp(' ')
        disp('TRANSFER FUNCTION')
        disp('------------------------------------------------------')

        disp(Gest)
        

        disp(['Fit = ',num2str(fit_tf),' %'])

        disp(['Natural frequency = ',...
            num2str(wn_tf),' rad/s'])

        disp(['Damping ratio = ',...
            num2str(zeta_tf)])


        disp(' ')
        disp('STATE SPACE')
        disp('------------------------------------------------------')

        disp(Gss)

        disp(['Fit = ',num2str(fit_ss),' %'])


        disp(' ')
        disp('STATE-SPACE MATRICES')
        disp('------------------------------------------------------')

        disp('A = ')
        disp(A)

        disp('B = ')
        disp(B)

        disp('C = ')
        disp(C)

        disp('D = ')
        disp(D)


        disp(' ')
        disp('POLES')
        disp('------------------------------------------------------')

        disp('TF poles:')
        disp(poles_tf)

        disp('SS poles:')
        disp(poles_ss)

    end

end


%% =============================================================
% =============================================================
%
%              MERGE ALL TRANSFER FUNCTION MODELS
%
% =============================================================
% =============================================================

disp(' ')
disp('======================================================')
disp('             MERGING TRANSFER FUNCTION MODELS')
disp('======================================================')


% Only models having the same structure can be merged.
%
% Each individual experiment/segment produced an idtf model:
%
%       G_TF_1
%       G_TF_2
%       G_TF_3
%       ...
%
% merge() combines them into one identified model.
%
% The resulting parameters are statistically weighted according
% to the parameter covariance of the individual models.


if ~isempty(TF_models_for_merge)

    GTF_merged = ...
        merge(TF_models_for_merge{:});


    %% ---------------------------------------------------------
    % Store merged TF
    % ----------------------------------------------------------

    results_merged.TF.model = GTF_merged;


    %% ---------------------------------------------------------
    % Extract merged TF coefficients
    % ----------------------------------------------------------

    [num_merged,den_merged] = ...
        tfdata(GTF_merged,'v');

    results_merged.TF.numerator = num_merged;

    results_merged.TF.denominator = den_merged;


    %% ---------------------------------------------------------
    % Merged poles
    % ----------------------------------------------------------

    results_merged.TF.poles = pole(GTF_merged);


    %% ---------------------------------------------------------
    % Merged natural frequency / damping
    % ----------------------------------------------------------

    if length(den_merged) == 3

        a1_merged = den_merged(2);
        a0_merged = den_merged(3);

        wn_merged = sqrt(abs(a0_merged));

        if wn_merged > 0

            zeta_merged = ...
                a1_merged/(2*wn_merged);

        else

            zeta_merged = NaN;

        end

    else

        a1_merged = NaN;
        a0_merged = NaN;
        wn_merged = NaN;
        zeta_merged = NaN;

    end


    results_merged.TF.a1 = a1_merged;

    results_merged.TF.a0 = a0_merged;

    results_merged.TF.wn = wn_merged;

    results_merged.TF.zeta = zeta_merged;


    disp(' ')
    disp('MERGED TRANSFER FUNCTION:')
    disp(GTF_merged)

    disp(' ')
    disp('Merged poles:')
    disp(results_merged.TF.poles)

    disp(' ')
    disp(['Merged natural frequency = ',...
        num2str(wn_merged),' rad/s'])

    disp(['Merged damping ratio = ',...
        num2str(zeta_merged)])

end


%% =============================================================
% =============================================================
%
%              MERGE ALL STATE-SPACE MODELS
%
% =============================================================
% =============================================================

disp(' ')
disp('======================================================')
disp('              MERGING STATE-SPACE MODELS')
disp('======================================================')


if ~isempty(SS_models_for_merge)

    GSS_merged = ...
        merge(SS_models_for_merge{:});


    %% ---------------------------------------------------------
    % Store merged SS
    % ----------------------------------------------------------

    results_merged.SS.model = GSS_merged;


    %% ---------------------------------------------------------
    % Extract merged matrices
    % ----------------------------------------------------------

    results_merged.SS.A = GSS_merged.A;

    results_merged.SS.B = GSS_merged.B;

    results_merged.SS.C = GSS_merged.C;

    results_merged.SS.D = GSS_merged.D;


    %% ---------------------------------------------------------
    % Merged poles
    % ----------------------------------------------------------

    results_merged.SS.poles = ...
        pole(GSS_merged);


    %% ---------------------------------------------------------
    % Display
    % ----------------------------------------------------------

    disp(' ')
    disp('MERGED STATE-SPACE MODEL:')
    disp(GSS_merged)

    disp(' ')
    disp('Merged A matrix:')
    disp(GSS_merged.A)

    disp(' ')
    disp('Merged B matrix:')
    disp(GSS_merged.B)

    disp(' ')
    disp('Merged C matrix:')
    disp(GSS_merged.C)

    disp(' ')
    disp('Merged D matrix:')
    disp(GSS_merged.D)

    disp(' ')
    disp('Merged poles:')
    disp(results_merged.SS.poles)

end


%% =============================================================
% =============================================================
%
%              CONVERT MERGED SS -> TF
%
% =============================================================
% =============================================================

if ~isempty(SS_models_for_merge)

    GSS_merged_tf = tf(GSS_merged);

    results_merged.SS.transfer_function = ...
        GSS_merged_tf;


    disp(' ')
    disp('======================================================')
    disp('        MERGED STATE-SPACE -> TRANSFER FUNCTION')
    disp('======================================================')

    disp(GSS_merged_tf)

end


%% =============================================================
% =============================================================
%
%              COMPARE MERGED MODELS
%
% =============================================================
% =============================================================

disp(' ')
disp('======================================================')
disp('             VALIDATING MERGED MODELS')
disp('======================================================')


% Create one figure containing all individual experiments.

figure()
hold on
grid on

title('Merged Transfer Function vs Individual Experiments')
xlabel('Time (s)')
ylabel('Angle (rad)')


%% =============================================================
% Plot individual experimental responses
% =============================================================

for i = 1:num_experiments

    for seg = 1:results(i).num_segments

        data_val = ...
            results(i).segment(seg).identification.data;

        if exist('GTF_merged','var')

            [yhat,fit] = compare(...
                data_val,...
                GTF_merged,...
                compareOptions('InitialCondition','z'));

            fit_merged_tf_all(i,seg) = fit;

        end

    end

end


%% =============================================================
% Compare merged TF and merged SS numerically
% =============================================================

if exist('GTF_merged','var') && ...
   exist('GSS_merged','var')

    disp(' ')
    disp('MERGED TF:')
    disp(GTF_merged)

    disp(' ')
    disp('MERGED SS:')
    disp(GSS_merged)

end


%% =============================================================
%                  SUMMARY TABLE
% =============================================================

summary_rows = [];

for i = 1:num_experiments

    for seg = 1:results(i).num_segments

        row.experiment = string(id(i,:));

        row.segment = seg;

        row.TF_fit = ...
            results(i).segment(seg).TF.fit_percent;

        row.SS_fit = ...
            results(i).segment(seg).SS.fit_percent;

        row.torque_amplitude = ...
            results(i).segment(seg).torque_amplitude;

        row.angle_amplitude = ...
            results(i).segment(seg).angle_amplitude_deg;

        row.TF_wn = ...
            results(i).segment(seg).TF.wn;

        row.TF_zeta = ...
            results(i).segment(seg).TF.zeta;

        summary_rows = ...
            [summary_rows; row];

    end

end


%% =============================================================
%                  SAVE EVERYTHING
% =============================================================

save(...
    'system_identification_results.mat',...
    'results',...
    'results_merged',...
    'Gest_all',...
    'Gss_all',...
    'fit_tf_all',...
    'fit_ss_all',...
    'fit_merged_tf_all',...
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

disp(' ')
disp('Individual models and merged models saved in:')
disp('system_identification_results.mat')


%% =============================================================
%              FUNCTION: EXTRACT 5 PERIODS
% =============================================================

function [segment,...
          t_segment,...
          idx_start,...
          idx_end] = ...
          extract_5_periods(t,signal)


% -------------------------------------------------------------
% Normalize signal
% -------------------------------------------------------------

signal_range = max(signal)-min(signal);

if signal_range == 0

    error('Signal has zero amplitude.')

end


sig_norm = ...
    (signal-min(signal)) / signal_range;


% -------------------------------------------------------------
% Sampling time
% -------------------------------------------------------------

dt = mean(diff(t));


% -------------------------------------------------------------
% Derivative
% -------------------------------------------------------------

dsig = diff(sig_norm)/dt;


% -------------------------------------------------------------
% Detect rising edges
% -------------------------------------------------------------

if length(dsig) < 6

    error('Not enough data to detect rising edges.')

end


sorted_dsig = ...
    sort(dsig(5:end),'descend');


if length(sorted_dsig) < 2

    error(...
        'Not enough data to detect rising edges.')

end


secondMax = sorted_dsig(2);

rise_thresh = ...
    0.20*secondMax;


is_rising = ...
    dsig > rise_thresh;


% -------------------------------------------------------------
% Find starts of rising edges
% -------------------------------------------------------------

rising_starts = ...
    find(diff([0;is_rising(:)]) == 1);


% -------------------------------------------------------------
% Check number of detected periods
% -------------------------------------------------------------

if length(rising_starts) < 7

    error(...
        ['Not enough periods detected. ',...
         'Found %d rising edges, need at least 7.'],...
        length(rising_starts))

end


% -------------------------------------------------------------
% Extract periods 2 -> 6
% -------------------------------------------------------------

idx_start = rising_starts(2);

idx_end = rising_starts(7)-1;


segment = ...
    signal(idx_start:idx_end);

t_segment = ...
    t(idx_start:idx_end);


%Estimate grey-box model 
init_params = {
    'J', J;
    'b', b;
    'k', k;
   };

capt_zero = idgrey(...
    'capt_init_model', ...
    init_params, ...
    'c');

capt_motor = greyest(data, capt_zero);

%parameter update 
[An, Bn, Cn, Dn] = ssdata(capt_motor);


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
