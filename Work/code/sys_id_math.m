```matlab
clear
close all
clc


%% =============================================================
%                      LOAD DATA
% =============================================================

load('exp_distance.mat')

id = ['100';'116';'098';'097';'095';'090';'085';'093';'092'];


%% =============================================================
%              INITIALIZE IDENTIFICATION STORAGE
% =============================================================

% One structure for each experiment
results = struct();

% Keep model objects separately if desired
Gest_all = {};
Gss_all  = {};

% Number of experiments
num_experiments = length(id);


%% =============================================================
%                  LOOP THROUGH EXPERIMENTS
% =============================================================

for i = 1:num_experiments

    experiment_id = id(i,:);

    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change=t_change',experiment_id,';'))


    %% =========================================================
    %                  BASIC SIGNAL EXTRACTION
    % ==========================================================

    time = data(:,1);

    % Encoder position
    angle = data(:,4);       % degrees

    % Default channel indices:
    % [force, torque_sent, iA_sent, iB_sent]
    c_idx = [5 7 9 8];


    %% =========================================================
    %                  CHANNEL / GAIN SELECTION
    % ==========================================================

    if str2num(experiment_id) < 92

        g = 1;

    elseif str2num(experiment_id) < 100

        c_idx = [6 8 10 9];
        g = 4;

    elseif str2num(experiment_id) < 110

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
        b,a,torque_load);


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
        % Convert degrees -> radians
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
            mean(abs(seg_sent-seg_load));

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


        gain_plateau(i,seg) = ...
            sum(seg_load(is_plateau).* ...
                seg_sent(is_plateau)) / ...
            sum(seg_sent(is_plateau).^2);


        rmse_plateau(i,seg) = ...
            sqrt(mean(...
            (seg_load(is_plateau)- ...
             seg_sent(is_plateau)).^2));


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


        if seg == 3

            xlabel("Time (s)")

            title([...
                'Experiment ',experiment_id,...
                ' - center: ',...
                num2str(mean(c_angle(i,:))),...
                ' deg'])

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
        %     measured load-cell torque
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
        %        Torque ---> Mechanical system ---> Angle
        %
        %        G(s) = Theta(s) / Torque(s)
        %
        % ======================================================
        % ======================================================


        %% =====================================================
        %                 PREPARE ID DATA
        % ======================================================

        Ts = mean(diff(seg_time));

        u = seg_load(:);
        y = seg_angle(:);

        % Remove mean torque
        u = u - mean(u);

        % Identification data
        data_id = iddata(...
            y,...
            u,...
            Ts);


        %% =====================================================
        %          IDENTIFICATION METHOD 1:
        %               TRANSFER FUNCTION
        % ======================================================

        Gest = tfest(...
            data_id,...
            2,...
            0,...
            NaN);


        %% =====================================================
        %          IDENTIFICATION METHOD 2:
        %                 STATE SPACE
        % ======================================================

        Gss = ssest(...
            data_id,...
            2);


        % Convert SS model to transfer function
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

        % Transfer function:
        %
        %       b0*s + b1
        % G = ---------------------
        %       s^2 + a1*s + a0
        %

        [num_tf,den_tf] = tfdata(...
            Gest,...
            'v');

        num_tf = num_tf(:).';
        den_tf = den_tf(:).';


        % Pad numerator if necessary
        if length(num_tf) < 2
            num_tf = [0 num_tf];
        end

        % Normalized second-order denominator
        if length(den_tf) == 3

            a1 = den_tf(2);
            a0 = den_tf(3);

            wn_tf = sqrt(a0);

            zeta_tf = ...
                a1/(2*wn_tf);

            poles_tf = pole(Gest);

        else

            a1 = NaN;
            a0 = NaN;
            wn_tf = NaN;
            zeta_tf = NaN;
            poles_tf = pole(Gest);

        end


        %% =====================================================
        %          PHYSICAL PARAMETERS FROM TF
        % ======================================================

        % For:
        %
        %       J*s^2 + b*s + k
        %
        % G(s) = 1/(J*s^2+b*s+k)
        %
        % normalized form:
        %
        %       1
        % G(s) = ----------------
        %        s^2 + b/J*s+k/J
        %
        %
        % Therefore:
        %
        %       k/J = a0
        %       b/J = a1
        %
        % and, if J is known:
        %
        %       k = J*a0
        %       b = J*a1
        %
        % -----------------------------------------------------

        % Put your known inertia here
        J_known = NaN;

        if ~isnan(J_known) && ...
           length(den_tf) == 3

            k_tf = J_known*a0;
            b_tf = J_known*a1;

        else

            k_tf = NaN;
            b_tf = NaN;

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
        %      SS NATURAL FREQUENCY AND DAMPING
        % ======================================================

        if length(poles_ss) == 2

            wn_ss = sqrt(abs(poles_ss(1)*poles_ss(2)));

            zeta_ss = ...
                -real(sum(poles_ss)) / ...
                (2*wn_ss);

        else

            wn_ss = NaN;
            zeta_ss = NaN;

        end


        %% =====================================================
        %              STORE EVERYTHING
        % ======================================================

        % General segment information

        results(i).segment(seg).segment_number = seg;

        results(i).segment(seg).Ts = Ts;

        results(i).segment(seg).center_deg = ...
            c_angle(i,seg);

        results(i).segment(seg).torque_amplitude = ...
            dTorque(i,seg);

        results(i).segment(seg).angle_amplitude_deg = ...
            d_angle(i,seg);


        % Torque tracking results

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
        % Store identification data
        % ------------------------------------------------------

        results(i).segment(seg).identification.input = u;

        results(i).segment(seg).identification.output = y;

        results(i).segment(seg).identification.data = data_id;


        %% -----------------------------------------------------
        % Store transfer function
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

        results(i).segment(seg).TF.k = k_tf;

        results(i).segment(seg).TF.b = b_tf;


        %% -----------------------------------------------------
        % Store state-space model
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
        % Store SS -> TF conversion
        % ------------------------------------------------------

        results(i).segment(seg).SS.transfer_function = Gss_tf;


        %% =====================================================
        %             STORE LEGACY ARRAYS
        % ======================================================

        Gest_all{i,seg} = Gest;
        Gss_all{i,seg} = Gss;

        fit_tf_all(i,seg) = fit_tf;
        fit_ss_all(i,seg) = fit_ss;


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
%              SAVE COMPLETE RESULTS
% =============================================================

save(...
    'system_identification_results.mat',...
    'results',...
    'Gest_all',...
    'Gss_all',...
    'fit_tf_all',...
    'fit_ss_all',...
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
disp('IDENTIFICATION COMPLETE')
disp('======================================================')

disp('Results saved to:')
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

sig_norm = ...
    (signal-min(signal)) / ...
    (max(signal)-min(signal));


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

end
%% =============================================================
%              MERGE IDENTIFIED MODELS
%
% Each experiment/segment has produced:
%
%   Gest_all{i,seg} = transfer-function model
%   Gss_all{i,seg}  = state-space model
%
% We now merge models having the SAME structure.
% =============================================================

disp(' ')
disp('======================================================')
disp('              MERGING IDENTIFIED MODELS')
disp('======================================================')


%% =============================================================
%                MERGE TRANSFER FUNCTIONS
% =============================================================

% Collect all valid TF models

TF_models = {};

for i = 1:num_experiments

    for seg = 1:size(Gest_all,2)

        if ~isempty(Gest_all{i,seg})

            TF_models{end+1} = Gest_all{i,seg};

        end

    end

end


% Start with the first TF model

GTF_merged = TF_models{1};


% Sequentially merge all remaining TF models

for n = 2:length(TF_models)

    GTF_merged = merge(GTF_merged,TF_models{n});

end


%% =============================================================
%                MERGE STATE-SPACE MODELS
% =============================================================

SS_models = {};

for i = 1:num_experiments

    for seg = 1:size(Gss_all,2)

        if ~isempty(Gss_all{i,seg})

            SS_models{end+1} = Gss_all{i,seg};

        end

    end

end


% Start with the first SS model

GSS_merged = SS_models{1};


% Sequentially merge all remaining SS models

for n = 2:length(SS_models)

    GSS_merged = merge(GSS_merged,SS_models{n});

end


%% =============================================================
%                  DISPLAY MERGED MODELS
% =============================================================

disp(' ')
disp('======================================================')
disp('              MERGED TRANSFER FUNCTION')
disp('======================================================')

disp(GTF_merged)


disp(' ')
disp('======================================================')
disp('              MERGED STATE-SPACE MODEL')
disp('======================================================')

disp(GSS_merged)


%% =============================================================
%          CONVERT MERGED SS -> TRANSFER FUNCTION
% =============================================================

GSS_merged_tf = tf(GSS_merged);

disp(' ')
disp('======================================================')
disp('       MERGED STATE-SPACE -> TRANSFER FUNCTION')
disp('======================================================')

disp(GSS_merged_tf)


%% =============================================================
%                  MERGED MODEL POLES
% =============================================================

disp(' ')
disp('Merged TF poles:')
disp(pole(GTF_merged))

disp(' ')
disp('Merged SS poles:')
disp(pole(GSS_merged))


%% =============================================================
%                    SAVE MERGED MODELS
% =============================================================

save(...
    'system_identification_results.mat',...
    'results',...
    'Gest_all',...
    'Gss_all',...
    'fit_tf_all',...
    'fit_ss_all',...
    'GTF_merged',...
    'GSS_merged',...
    'GSS_merged_tf',...
    '-append')


disp(' ')
disp('Merged models saved.')





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
