clear
close all
clc

% =============================================================
% LOAD DATA
% =============================================================

load('exp_distance.mat')

id = ['100';'116';'098';'097';'095';'090';'085';'093';'092'];


%% =============================================================
% LOOP THROUGH EXPERIMENTS
% =============================================================

for i = 1:length(id)

    experiment_id = id(i,:);

    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change=t_change',experiment_id,';'))

    % t_change contains the time instants separating the segments

    time = data(:,1);

    % Recorded encoder position
    angle = data(:,4);      % degrees

    % force, torque_sent, iA_sent, iB_sent
    c_idx = [5 7 9 8];


    %% =========================================================
    % CHANNEL / GAIN SELECTION
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
    % EXTRACT SIGNALS
    % ==========================================================

    force = data(:,c_idx(1));

    % Commanded torque
    torque_sent = -data(:,c_idx(2))*g;

    % Sent motor currents
    iA_sent = data(:,c_idx(3));
    iB_sent = data(:,c_idx(4));


    %% =========================================================
    % FILTERING
    % ==========================================================

    fs = 1/mean(diff(time));

    fc = 20;

    [b,a] = butter(8,fc/(fs/2),'low');


    %% =========================================================
    % LOAD CELL FORCE -> TORQUE
    % ==========================================================

    torque_load = force*0.0846;

    filtered_torque_load = filtfilt(b,a,torque_load);


    %% =========================================================
    % PRELOAD
    % ==========================================================

    torque_preload = mean(torque_sent);

    load_preload = mean(filtered_torque_load);

    center(i) = mean(angle);


    %% =========================================================
    % FIGURE 1: COMPLETE EXPERIMENT
    % ==========================================================

    figure()

    subplot(3,1,1)

    plot(time,...
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

    plot(time,...
        angle,...
        'LineWidth',1)

    hold on

    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    ylabel("Angle (deg)")


    subplot(3,1,3)

    plot(time,...
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
    % FIND SEGMENT INDICES
    % ==========================================================

    event_idx = zeros(size(t_change));

    for k = 1:length(t_change)

        [~,event_idx(k)] = ...
            min(abs(time-t_change(k)));

    end

    num_segments = length(event_idx)-1;


    %% =========================================================
    % FIGURE 2: TORQUE TRACKING SEGMENTS
    % ==========================================================

    figure()


    %% =========================================================
    % LOOP THROUGH SEGMENTS
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
        % Extract corresponding encoder angle
        % ------------------------------------------------------

        seg_angle_deg = ...
            angle(...
            i_start0+i_start : ...
            i_start0+i_end);


        % Convert degrees -> radians
        seg_angle = deg2rad(seg_angle_deg);


        %% -----------------------------------------------------
        % Center angle around zero
        % ------------------------------------------------------

        % For mechanical identification, remove the mean position
        % so that the stiffness term represents displacement from
        % the equilibrium position.

        seg_angle = ...
            seg_angle - mean(seg_angle);


        %% =====================================================
        % ANGLE ANALYSIS
        % ======================================================

        c_angle(i,seg) = mean(seg_angle_deg);


        [pks_max,~] = findpeaks(seg_angle_deg);

        [pks_min,~] = findpeaks(-seg_angle_deg);

        pks_min = -pks_min;


        if length(pks_max) >= 5 && length(pks_min) >= 5

            pks_max = maxk(pks_max,5);
            pks_min = mink(pks_min,5);

            d_angle(i,seg) = ...
                mean(pks_max)-mean(pks_min);

        else

            d_angle(i,seg) = NaN;

        end


        %% =====================================================
        % TORQUE TRACKING ANALYSIS
        % ======================================================

        dTorque(i,seg) = ...
            max(seg_sent)-min(seg_sent);


        %% -----------------------------------------------------
        % Correlation
        % ------------------------------------------------------

        [R,P] = corrcoef(seg_sent,seg_load);

        r(i,seg) = R(1,2);
        p(i,seg) = P(1,2);


        %% -----------------------------------------------------
        % MAE
        % ------------------------------------------------------

        rm(i,seg) = ...
            mean(abs(seg_sent-seg_load));

        rm_perc(i,seg) = ...
            rm(i,seg) / ...
            (max(seg_sent)-min(seg_sent));


        %% -----------------------------------------------------
        % R-squared
        % ------------------------------------------------------

        SS_res = ...
            sum((seg_sent-seg_load).^2);

        SS_tot = ...
            sum((seg_sent-mean(seg_load)).^2);

        R2(i,seg) = ...
            1-SS_res/SS_tot;


        %% =====================================================
        % PLATEAU / EDGE ANALYSIS
        % ======================================================

        dx = gradient(seg_sent);

        thr = ...
            0.05*max(abs(dx(5:end)));

        is_plateau = abs(dx) < thr;

        is_edge = ~is_plateau;


        %% Plateau gain

        gain_plateau(i,seg) = ...
            sum(seg_load(is_plateau).* ...
                seg_sent(is_plateau)) / ...
            sum(seg_sent(is_plateau).^2);


        %% Plateau RMSE

        rmse_plateau(i,seg) = ...
            sqrt(mean(...
            (seg_load(is_plateau)- ...
             seg_sent(is_plateau)).^2));


        %% Edge RMSE

        rmse_edge(i,seg) = ...
            sqrt(mean(...
            (seg_sent(is_edge)- ...
             seg_load(is_edge)).^2));


        %% =====================================================
        % PLOT TORQUE TRACKING
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
        % SYSTEM IDENTIFICATION
        %
        % INPUT:
        %   measured physical torque = seg_load
        %
        % OUTPUT:
        %   encoder angle = seg_angle
        %
        % Therefore:
        %
        %       torque -> mechanical system -> angle
        %
        %       G(s) = Theta(s) / Torque(s)
        % ======================================================

        Ts = mean(diff(seg_time));


        % Make sure input and output are column vectors
        u = seg_load(:);
        y = seg_angle(:);


        %% Remove DC component from torque

        u = u - mean(u);


        %% Create identification data

        data_id = iddata(y,u,Ts);


        %% Estimate second-order transfer function

        Gest = tfest(...
            data_id,...
            2,...
            0,...
            NaN);


        %% Store identified model

        Gest_all{i,seg} = Gest;


        %% =====================================================
        % IDENTIFICATION FIGURE
        % ======================================================

        figure()

        compare(data_id,Gest)

        grid on

        title([...
            'System Identification - Experiment ',...
            experiment_id,...
            ', Segment ',...
            num2str(seg)])

        set(...
            findall(gcf,'Type','Line'),...
            'LineWidth',2)


        %% =====================================================
        % DISPLAY IDENTIFIED MODEL
        % ======================================================

        disp(' ')
        disp('==============================================')
        disp(['Experiment: ',experiment_id])
        disp(['Segment: ',num2str(seg)])
        disp('Input  = measured load-cell torque [Nm]')
        disp('Output = encoder angle [rad]')
        disp('Identified transfer function:')
        disp(Gest)
        disp('==============================================')


    end
    
%New fit 
Gss = ssest(data_id, 1:10);
Gest_new = tf(Gss);
%Obtain model comparison 2
opt = compareOptions;
opt.InitialCondition = 'z';
figure;
compare(data_id,Gest,opt);
grid on;
set(findall(gca, 'Type', 'Line'), 'LineWidth', 4');



end


%% =============================================================
% FUNCTION TO DETECT 5 PERIODS
% =============================================================

function [segment,...
          t_segment,...
          idx_start,...
          idx_end] = ...
          extract_5_periods(t,signal)


% Normalize signal

sig_norm = ...
    (signal-min(signal)) / ...
    (max(signal)-min(signal));


% Sampling time

dt = mean(diff(t));


% Derivative

dsig = diff(sig_norm)/dt;


% Detect rising edges

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


% Find starts of rising edges

rising_starts = ...
    find(diff([0;is_rising(:)]) == 1);


% Check number of detected periods

if length(rising_starts) < 7

    error(...
        ['Not enough periods detected. ',...
         'Found %d rising edges, need at least 7.'],...
        length(rising_starts))

end


% Extract periods 2 -> 6

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
