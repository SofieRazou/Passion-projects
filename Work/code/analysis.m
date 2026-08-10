clear
close all
clc

% load('exp103-109_distance.mat')
% id=['109';'108';'103';'104';'105';'106';'107'];
load('exp_distance.mat')
id=['100';'116';'098';'097';'095';'090';'085';'093';'092'];

% Initialize matrix to accumulate sorted data across experiments/segments
exp_sorted = [];

%% Loop through experiments
for i=1:length(id)
    experiment_id = id(i,:);
    eval(strcat('data=exp',experiment_id,';'))
    eval(strcat('t_change = t_change',experiment_id,';')) % Could be taken from the last part of the exp
    time = data(:,1);
    % iA_rec = data(:,2);   % recorded current Ch1 = ch8 = -sen
    % iB_rec = data(:,3);   % recorded current Ch2 = ch16 = cos
    angle = data(:,4);      % encoder position (deg)
    c_idx=[5 7 9 8]; %      force torque_sent iA_sent iB_sent
    if str2num(experiment_id)<92 
        g = 1;
    elseif str2num(experiment_id)<100
        c_idx=[6 8 10 9];
        g = 4;
    elseif str2num(experiment_id)<110
        g = 4;
    else
        g = 1;
        angle=angle-58.1;
    end
    force = data(:,c_idx(1));      % load cell recorded force
    torque_sent = -data(:,c_idx(2))*g;  % commanded torque
    iA_sent = data(:,c_idx(3));  % sent current to ch8
    iB_sent = data(:,c_idx(4));  % sent current to ch16
    fs = 1/mean(diff(time));
    fc = 20;
    [b, a] = butter(8, fc/(fs/2), 'low'); % low-pass butterworth filter
    torque_load = force*0.0846; % torque read by the load cell (N) * radius (m)
    filtered_torque_load = filtfilt(b, a, torque_load); % filtering
    torque_preload = mean(torque_sent);
    load_preload = mean(filtered_torque_load);
    center(i) = mean(angle);
    
    figure()
    subplot(3,1,2)
    plot(time, angle,'LineWidth',1)
    hold on
    xline(t_change)
    ylabel("angle (deg)")
    
    subplot(3,1,1)
    plot(time,torque_sent, 'Color', [.4 .4 .4],'LineWidth',1)
    hold on
    xline(t_change)
    ylabel("commanded torque (Nm)")
    
    subplot(3,1,3)
    plot(time,filtered_torque_load-load_preload+torque_preload, 'Color', [.8 .3 .2],'LineWidth',1)
    hold on
    xline(t_change)
    xlabel("time (s)")
    ylabel("load cell torque (Nm)")
    
    event_idx = zeros(size(t_change));
    for k = 1:length(t_change)
        [~, event_idx(k)] = min(abs(time - t_change(k)));
    end
    num_segments = length(event_idx) - 1;
    
    figure()
    for seg = 1:num_segments
        i_start0 = event_idx(seg);
        i_end   = event_idx(seg + 1);
        seg_t   = time(i_start0:i_end);
        seg_torque_sent = torque_sent(i_start0:i_end)-torque_preload;
        
        % Cutting 5 periods based on the sent torque
        [seg_sent, seg_time, i_start,i_end] = extract_5_periods(seg_t, seg_torque_sent);
        seg_load = filtered_torque_load(i_start0+i_start:i_end+i_start0)-load_preload;
        
        % angle analysis
        seg_angle = angle(i_start0+i_start:i_end+i_start0);
        c_angle(i,seg)=mean(seg_angle);
        [pks_max, ~] = findpeaks(seg_angle);
        
        % Find minima
        [pks_min, ~] = findpeaks(-seg_angle);
        pks_min = -pks_min;
        
        % Keep the 5 largest maxima and 5 lowest minima
        pks_max = maxk(pks_max,5);
        pks_min = mink(pks_min,5);
        
        % peak-to-peak angular displacement
        d_angle(i,seg) = mean(pks_max) - mean(pks_min);
        dTorque(i,seg)=max(seg_sent)-min(seg_sent);
        
        % correlation coefficient
        [R,P] = corrcoef(seg_sent,seg_load);
        r(i,seg)=R(1,2); % correlation coeff
        p(i,seg)=P(1,2); % p-value of correlation coeff
        
        % global RMSE
        rm(i,seg)=mean(abs(seg_sent-seg_load));
        rm_perc(i,seg)=rm(i,seg)./(max(seg_sent)-min(seg_sent));
        
        % R-squared
        SS_res = sum((seg_sent - seg_load).^2);
        SS_tot = sum((seg_sent - mean(seg_load)).^2);
        R2(i,seg) = 1 - SS_res/SS_tot;
        
        % rmse divided between rising/falling and plateaux
        N = length(seg_sent);
        dx = gradient(seg_sent);
        thr = 0.05 * max(abs(dx(5:end)));
        is_plateau = abs(dx) < thr;
        is_edge = ~is_plateau;
        gain_plateau(i,seg) = sum(seg_load(is_plateau).*seg_sent(is_plateau)) / sum(seg_sent(is_plateau).^2);
        rmse_plateau(i,seg) = sqrt(mean(seg_load(is_plateau) - seg_sent(is_plateau)).^2);
        rmse_edge(i,seg) = sqrt(mean((seg_sent(is_edge) - seg_load(is_edge)).^2));
        
        % Append extracted segment data into exp_sorted matrix
        % Col 1: seg_angle | Col 2: seg_load | Col 3: seg_time
        current_segment_data = [seg_angle(:), seg_load(:), seg_time(:)];
        exp_sorted = [exp_sorted; current_segment_data];
        
        subplot(num_segments,1,seg)
        plot(seg_time-seg_time(1),seg_sent+torque_preload, 'Color', [.4 .4 .4],'LineWidth',1)
        hold on
        plot(seg_time-seg_time(1),seg_load+torque_preload, 'Color', [.8 .3 .2],'LineWidth',1)
        xlim([0,seg_time(end)-seg_time(1)])
        ylabel("shifted torque (Nm)")
        if seg ==3
            xlabel("time (s)")
            title(['center: ',num2str(mean(c_angle(i,:))),' deg'])
        end
        clear R P
    end
end

%% Save to exp_sorted.mat
save('exp_sorted.mat', 'exp_sorted');
disp('Saved exp_sorted.mat successfully!');

%% Subfunction to detect 5 periods
function [segment, t_segment, idx_start, idx_end] = extract_5_periods(t, signal)
% EXTRACT_5_PERIODS - Extracts 5 full periods from a trapezoidal wave
sig_norm = (signal - min(signal)) / (max(signal) - min(signal));

dt = mean(diff(t));
dsig = diff(sig_norm) / dt;

sorted_dsig = sort(dsig(5:end), 'descend');
secondMax = sorted_dsig(2);
rise_thresh = 0.20 * secondMax;
is_rising = dsig > rise_thresh;

rising_starts = find(diff([0; is_rising(:)]) == 1);

if length(rising_starts) < 7
    error('Not enough periods detected. Found %d rising edges, need at least 5.', ...
        length(rising_starts));
end

idx_start = rising_starts(2);
idx_end   = rising_starts(7) - 1;  % just before the 6th period starts
segment   = signal(idx_start : idx_end);
t_segment = t(idx_start : idx_end);
end
