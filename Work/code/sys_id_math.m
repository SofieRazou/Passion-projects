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

Gest_all = {};
Gss_all  = {};

fit_tf_all = [];
fit_ss_all = [];



%% =============================================================
%                  LOOP THROUGH EXPERIMENTS
% =============================================================

for i = 1:length(id)

    experiment_id = id(i,:);

    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change=t_change',experiment_id,';'))

    % t_change contains the time instants separating the segments


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
    %
    % This is ONLY DATA PROCESSING / VISUALIZATION.
    % No system identification is performed here.
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
    %              FIGURE 2: TORQUE TRACKING
    %
    % Again, this section is ONLY processing/analysis.
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
        % THIS WILL BE THE IDENTIFICATION INPUT
        % ------------------------------------------------------

        seg_load = ...
            filtered_torque_load(...
            i_start0+i_start : ...
            i_start0+i_end) ...
            - load_preload;



        %% -----------------------------------------------------
        % Extract encoder angle
        %
        % THIS WILL BE THE IDENTIFICATION OUTPUT
        % ------------------------------------------------------

        seg_angle_deg = ...
            angle(...
            i_start0+i_start : ...
            i_start0+i_end);



        %% -----------------------------------------------------
        % Convert angle from degrees -> radians
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
        %        Torque  --->  Mechanical system  --->  Angle
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


        % Create System Identification Toolbox data object
        data_id = iddata(...
            y,...
            u,...
            Ts);


        %% =====================================================
        %          IDENTIFICATION METHOD 1:
        %               TRANSFER FUNCTION
        % ======================================================

        % Estimate a second-order transfer function.
        %
        % Expected mechanical structure:
        %
        %             1
        % G(s) = -----------
        %        Js^2+bs+k
        %
        % tfest estimates a generic second-order model.

        Gest = tfest(...
            data_id,...
            2,...
            0,...
            NaN);


        % Store model

        Gest_all{i,seg} = Gest;


        %% =====================================================
        %          IDENTIFICATION METHOD 2:
        %                 STATE SPACE
        % ======================================================

        % A second-order state-space model is used:
        %
        % x1 = theta
        % x2 = theta_dot
        %
        % x_dot = A*x + B*u
        % y     = C*x + D*u
        %
        % For the physical mechanical system:
        %
        %       J*theta_ddot + b*theta_dot + k*theta = tau
        %
        % the state-space representation is:
        %
        % [theta_dot ]   [ 0       1 ] [theta    ]
        % [theta_ddot] = [-k/J   -b/J] [theta_dot]
        %
        %                    [ 0 ]
        %              +     [1/J] tau
        %
        % and:
        %
        % y = [1 0] x
        %
        % Here ssest first estimates a generic state-space model.

        Gss = ssest(...
            data_id,...
            2);


        % Convert state-space model to transfer function
        % so that it can be directly compared with Gest.

        Gss_tf = tf(Gss);


        % Store models

        Gss_all{i,seg} = Gss;



        %% =====================================================
        %             COMPARE TRANSFER FUNCTION
        %             AND STATE-SPACE MODELS
        % ======================================================

        figure()

        compare(...
            data_id,...
            Gest,...
            Gss);

        grid on

        title([...
            'TF vs State-Space Identification - ',...
            'Experiment ',experiment_id,...
            ', Segment ',num2str(seg)])


        set(...
            findall(gcf,'Type','Line'),...
            'LineWidth',2)


        legend(...
            'Measured data',...
            'Transfer function',...
            'State-space',...
            'Location','best')



        %% =====================================================
        %                 MODEL FIT VALUES
        % ======================================================

        % Calculate fit percentages separately.

        [~,fit_tf] = compare(...
            data_id,...
            Gest);

        [~,fit_ss] = compare(...
            data_id,...
            Gss);


        fit_tf_all(i,seg) = fit_tf;

        fit_ss_all(i,seg) = fit_ss;



        %% =====================================================
        %                 DISPLAY RESULTS
        % ======================================================

        disp(' ')
        disp('======================================================')
        disp(['Experiment: ',experiment_id])
        disp(['Segment:    ',num2str(seg)])
        disp('======================================================')

        disp(' ')
        disp('IDENTIFICATION DATA:')
        disp('Input  = measured load-cell torque [Nm]')
        disp('Output = encoder angle [rad]')

        disp(' ')
        disp('------------------------------------------------------')
        disp('TRANSFER FUNCTION MODEL')
        disp('------------------------------------------------------')

        disp(Gest)

        disp(['Fit = ',num2str(fit_tf),' %'])


        disp(' ')
        disp('------------------------------------------------------')
        disp('STATE-SPACE MODEL')
        disp('------------------------------------------------------')

        disp(Gss)

        disp(['Fit = ',num2str(fit_ss),' %'])


        disp(' ')
        disp('STATE-SPACE MODEL CONVERTED TO TRANSFER FUNCTION')
        disp('------------------------------------------------------')

        disp(Gss_tf)



        %% =====================================================
        %          POLES / NATURAL DYNAMICS
        % ======================================================

        disp(' ')
        disp('POLES OF TRANSFER FUNCTION MODEL:')

        disp(pole(Gest))


        disp(' ')
        disp('POLES OF STATE-SPACE MODEL:')

        disp(pole(Gss))



    end

end



%% =============================================================
%              SUMMARY OF IDENTIFICATION RESULTS
% =============================================================

disp(' ')
disp('======================================================')
disp('              IDENTIFICATION SUMMARY')
disp('======================================================')


for i = 1:length(id)

    for seg = 1:num_segments

        disp([...
            'Experiment ',id(i,:),...
            ', Segment ',num2str(seg),...
            ': TF fit = ',...
            num2str(fit_tf_all(i,seg)),...
            ' %, SS fit = ',...
            num2str(fit_ss_all(i,seg)),...
            ' %'])

    end

end



%% =============================================================
%                 FUNCTION: EXTRACT 5 PERIODS
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
