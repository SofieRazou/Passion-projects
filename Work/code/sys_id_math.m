clear
close all
clc

% load('exp103-109_distance.mat')
% id=['109';'108';'103';'104';'105';'106';'107'];

load('exp_distance.mat')
id = ['100';'116';'098';'097';'095';'090';'085';'093';'092'];

%%

for i = 1:length(id)

    experiment_id = id(i,:);

    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change=t_change',experiment_id,';')) 
    % t_change contains the time instants separating the different segments

    time = data(:,1);

    % iA_rec = data(:,2);   % recorded current Ch1 = ch8 = -sen
    % iB_rec = data(:,3);   % recorded current Ch2 = ch16 = cos

    angle = data(:,4);      % encoder position (deg)

    c_idx = [5 7 9 8];      % force, torque_sent, iA_sent, iB_sent

    if str2num(experiment_id) < 92

        g = 1;

    elseif str2num(experiment_id) < 100

        c_idx = [6 8 10 9];
        g = 4;

    elseif str2num(experiment_id) < 110

        g = 4;

    else

        g = 1;
        angle = angle - 58.1;

    end

    %% Extract signals

    force = data(:,c_idx(1));      
    % load cell recorded force

    torque_sent = -data(:,c_idx(2))*g;  
    % commanded torque

    iA_sent = data(:,c_idx(3));    
    % sent current to ch8

    iB_sent = data(:,c_idx(4));    
    % sent current to ch16


    %% Filtering

    fs = 1/mean(diff(time));
    fc = 20;

    [b,a] = butter(8,fc/(fs/2),'low');

    %% Convert load-cell force to torque

    torque_load = force*0.0846;

    filtered_torque_load = filtfilt(b,a,torque_load);


    %% Preload

    torque_preload = mean(torque_sent);
    load_preload = mean(filtered_torque_load);

    center(i) = mean(angle);


    %% =========================================================
    % FIGURE 1: COMPLETE EXPERIMENT
    % ==========================================================

    figure()

    subplot(3,1,2)

    plot(time,angle,'LineWidth',1)
    hold on

    % Plot all t_change values individually
    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    ylabel("angle (deg)")
    title(['Experiment ',experiment_id])


    subplot(3,1,1)

    plot(time,torque_sent,...
        'Color',[.4 .4 .4],...
        'LineWidth',1)

    hold on

    % Plot all t_change values individually
    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    ylabel("commanded torque (Nm)")


    subplot(3,1,3)

    plot(time,...
        filtered_torque_load-load_preload+torque_preload,...
        'Color',[.8 .3 .2],...
        'LineWidth',1)

    hold on

    % Plot all t_change values individually
    for k = 1:length(t_change)
        xline(t_change(k),'--');
    end

    xlabel("time (s)")
    ylabel("load cell torque (Nm)")


    %% =========================================================
    % FIND INDICES CORRESPONDING TO t_change
    % ==========================================================

    event_idx = zeros(size(t_change));

    for k = 1:length(t_change)

        [~,event_idx(k)] = min(abs(time-t_change(k)));

    end

    num_segments = length(event_idx)-1;


    %% =========================================================
    % FIGURE 2: FIVE PERIODS FOR EACH SEGMENT
    % ==========================================================

    figure()

    for seg = 1:num_segments

        %% Extract segment

        i_start0 = event_idx(seg);
        i_end0   = event_idx(seg+1);

        seg_t = time(i_start0:i_end0);

        seg_torque_sent = ...
            torque_sent(i_start0:i_end0)-torque_preload;


        %% Extract 5 complete periods

        [seg_sent,...
         seg_time,...
         i_start,...
         i_end] = extract_5_periods(...
         seg_t,...
         seg_torque_sent);


        %% Extract corresponding measured torque

        seg_load = ...
            filtered_torque_load(...
            i_start0+i_start : ...
            i_end+i_start0) ...
            - load_preload;


        %% =====================================================
        % ANGLE ANALYSIS
        % ======================================================

        seg_angle = ...
            angle(i_start0+i_start : ...
                  i_end+i_start0);


        c_angle(i,seg) = mean(seg_angle);


        %% Find maxima

        [pks_max,~] = findpeaks(seg_angle);


        %% Find minima

        [pks_min,~] = findpeaks(-seg_angle);

        pks_min = -pks_min;


        %% Keep 5 largest maxima and 5 lowest minima

        pks_max = maxk(pks_max,5);
        pks_min = mink(pks_min,5);


        %% Peak-to-peak angular displacement

        d_angle(i,seg) = ...
            mean(pks_max)-mean(pks_min);


        %% Torque amplitude

        dTorque(i,seg) = ...
            max(seg_sent)-min(seg_sent);


        %% =====================================================
        % CORRELATION
        % ======================================================

        [R,P] = corrcoef(seg_sent,seg_load);

        r(i,seg) = R(1,2);
        p(i,seg) = P(1,2);


        %% =====================================================
        % GLOBAL MAE
        % ======================================================

        rm(i,seg) = ...
            mean(abs(seg_sent-seg_load));

        rm_perc(i,seg) = ...
            rm(i,seg) / ...
            (max(seg_sent)-min(seg_sent));


        %% =====================================================
        % R-SQUARED
        % ======================================================

        SS_res = ...
            sum((seg_sent-seg_load).^2);

        SS_tot = ...
            sum((seg_sent-mean(seg_load)).^2);

        R2(i,seg) = ...
            1-SS_res/SS_tot;


        %% =====================================================
        % PLATEAU / EDGE ANALYSIS
        % ======================================================

        N = length(seg_sent);

        dx = gradient(seg_sent);

        thr = ...
            0.05*max(abs(dx(5:end)));

        is_plateau = abs(dx) < thr;

        is_edge = ~is_plateau;


        %% Gain on plateau

        gain_plateau(i,seg) = ...
            sum(seg_load(is_plateau).* ...
                seg_sent(is_plateau)) / ...
            sum(seg_sent(is_plateau).^2);


        %% Plateau RMSE

        rmse_plateau(i,seg) = ...
            sqrt(mean(...
            (seg_load(is_plateau) - ...
             seg_sent(is_plateau)).^2));


        %% Edge RMSE

        rmse_edge(i,seg) = ...
            sqrt(mean(...
            (seg_sent(is_edge) - ...
             seg_load(is_edge)).^2));


        %% =====================================================
        % PLOT SEGMENT
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

        xlim([...
            0,...
            seg_time(end)-seg_time(1)])

        ylabel("Torque (Nm)")

        if seg == 3

            xlabel("time (s)")

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


        clear R P

    end

end


%% =============================================================
% FUNCTION TO DETECT 5 PERIODS
% =============================================================

function [segment,...
          t_segment,...
          idx_start,...
          idx_end] = extract_5_periods(t,signal)

% EXTRACT_5_PERIODS
%
% Extracts 5 complete periods from a trapezoidal wave.
%
% INPUTS:
%   t       - time vector
%   signal  - trapezoidal wave
%
% OUTPUTS:
%   segment    - extracted signal
%   t_segment - corresponding time vector
%   idx_start - start index
%   idx_end   - end index


%% Step 1: Normalize signal

sig_norm = ...
    (signal-min(signal)) / ...
    (max(signal)-min(signal));


%% Step 2: Sampling time

dt = mean(diff(t));


%% Step 3: Derivative

dsig = diff(sig_norm)/dt;


%% Step 4: Detect rising edges

sorted_dsig = ...
    sort(dsig(5:end),'descend');

secondMax = sorted_dsig(2);

rise_thresh = ...
    0.20*secondMax;

is_rising = ...
    dsig > rise_thresh;


%% Step 5: Find starts of rising edges

rising_starts = ...
    find(diff([0;is_rising(:)]) == 1);


%% Check number of detected periods

if length(rising_starts) < 7

    error(...
        'Not enough periods detected. Found %d rising edges, need at least 7.',...
        length(rising_starts));

end


%% Step 6: Extract 5 complete periods

idx_start = rising_starts(2);

idx_end = rising_starts(7)-1;


segment = ...
    signal(idx_start:idx_end);

t_segment = ...
    t(idx_start:idx_end);
%%Perform system identification based on zero kappa rendering experiment
%%wth load cell
Ts = 0.01; %sample time in sec
%Data collection with said input and output tracking
dt = Ts;
t = 0:dt:5;

u = seg_load;
yreal = seg_angle;


figure;
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
figure;
compare(data,Gest,opt);
grid on;
set(findall(gca, 'Type', 'Line'), 'LineWidth', 4');

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
