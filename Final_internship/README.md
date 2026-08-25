clear
close all
clc

% =============================================================
% 1. PURE STIFFNESS (k-only) THEORETICAL TRANSFER FUNCTION & BODE
% =============================================================
J_val = 0.0103;            % Fixed motor inertia
k_avg = 42.95 + 1;         % Average estimated stiffness
b_avg = 9.1079;

num = [1];
den = [J_val, b_avg, k_avg]; 
sys_k_only = tf(num, den);

disp('--- PURE STIFFNESS TRANSFER FUNCTION (b=0) ---');
disp(sys_k_only);

% Plot Theoretical Bode Diagram
figure('Name', 'k-Only System Bode Diagram');
bode(sys_k_only);
grid on;
title(sprintf('Theoretical Bode Plot (k = %.2f, b = %.2f)', k_avg, b_avg));


% =============================================================
% 2. CONFIGURE UDP RECEIVER
% =============================================================
localPort = 50000;
udpRx = dsp.UDPReceiver('LocalIPPort', localPort, ...
                        'MaximumMessageLength', 1024, ...
                        'MessageDataType', 'uint8');
setup(udpRx);

disp('========================================================');
disp(' Listening for dSPACE UDP data stream on port 50000...  ');
disp(' (Will automatically stop & plot after 2s of silence)   ');
disp('========================================================');

time_data = [];
angle_data = [];
torque_data = [];

fig = figure('Name', 'Live dSPACE Data Receiver', 'Position', [100, 100, 800, 500]);

% Timeout parameters
inactivityTimeout = 2.0; % Seconds to wait before stopping automatically
tic;                    % Start inactivity timer

try
    while true
        rawBytes = udpRx();
        
        if ~isempty(rawBytes)
            % Reset inactivity timer since a packet just arrived
            tic; 
            
            rawString = char(rawBytes');
            dataPacket = jsondecode(rawString);
            
            t_elapsed = dataPacket.elapsed_time;
            angle_val = dataPacket.Out1;
            torque_val = dataPacket.Torque;
            
            time_data(end+1, 1) = t_elapsed;
            angle_data(end+1, 1) = angle_val;
            torque_data(end+1, 1) = torque_val;
            
            fprintf('Time: %.2fs | Angle: %.4f | Torque: %.4f\n', t_elapsed, angle_val, torque_val);
            
            if length(time_data) > 1
                subplot(2,1,1);
                plot(time_data, angle_data, 'b-', 'LineWidth', 1.2);
                grid on;
                ylabel('Angle / Out1');
                title('Live dSPACE Data Stream');
                
                subplot(2,1,2);
                plot(time_data, torque_data, 'r-', 'LineWidth', 1.2);
                grid on;
                xlabel('Elapsed Time [s]');
                ylabel('Torque [Nm]');
                
                drawnow limitrate;
            end
        else
            % Check if we've exceeded the inactivity timeout window
            if toc > inactivityTimeout
                disp('--- UDP stream inactivity timeout reached. Processing Bode plots... ---');
                break;
            end
        end
    end

catch ME
    disp(['Receiver stopped: ', ME.message]);
end

% Release the UDP resource
release(udpRx);
disp('UDP receiver closed.');


% =============================================================
% 3. EMPIRICAL MODEL & BODE PLOT (Post-processing Recorded Data)
% =============================================================
if length(time_data) > 10
    % Calculate uniform sample time
    Ts = mean(diff(time_data));
    
    % Create an iddata object (Input: Torque, Output: Angle/Out1)
    data = iddata(angle_data, torque_data, Ts);
    
    % Estimate transfer function model from recorded stream (Empirical)
    sys_empirical = tfest(data, 2, 1);
    
    % Generate the Empirical Bode Plot in a new figure window
    figure('Name', 'System Identification - Empirical Bode Plot', 'Position', [200, 200, 700, 500]);
    bode(sys_empirical);
    grid on;
    title('Bode Plot of Empirical dSPACE System');
    disp('Empirical Bode plot generated successfully.');
    
    % =============================================================
    % 4. ACTUAL (THEORETICAL MODEL BASED ON MEASURED DATA) BODE PLOT
    % =============================================================
    % Build the actual/theoretical transfer function using your physical parameters
    % Input: Torque, Output: Angle
    sys_actual = tf([1], [J_val, b_avg, k_avg]);
    
    % Generate the Actual/Theoretical Bode Plot in a separate figure window
    figure('Name', 'System Identification - Actual Theoretical Bode Plot', 'Position', [300, 200, 700, 500]);
    bode(sys_actual);
    grid on;
    title(sprintf('Bode Plot of Actual Model (J=%.4f, b=%.4f, k=%.2f)', J_val, b_avg, k_avg));
    disp('Actual theoretical Bode plot generated successfully.');
else
    disp('Not enough data collected to generate reliable Bode plots.');
end
% =============================================================
% 3. DIRECT NON-PARAMETRIC BODE PLOT (Angle & Torque Measurements Only)
% =============================================================
if length(time_data) > 20
    % Calculate uniform sample time
    dt = mean(diff(time_data));
    Fs = 1 / dt; % Sampling frequency
    
    % Detrend data to remove any DC biases or offsets
    torque_clean = detrend(torque_data);
    angle_clean = detrend(angle_data);
    
    % Compute direct Frequency Response Estimate 
    % This divides the angle/torque data into windows to calculate the direct ratio
    [H, freq_vector] = tfestimate(torque_clean, angle_clean, [], [], [], Fs);
    
    % Convert frequency vector from Hz to rad/s for standard Bode plotting
    omega = freq_vector * 2 * pi;
    
    % Convert magnitude to decibels (dB) and phase to degrees
    mag_dB = 20 * log10(abs(H));
    phase_deg = unwrap(angle(H)) * (180 / pi);
    
    % Plot the Direct Measured Bode Diagram
    figure('Name', 'Direct Measured Bode Plot (Angle vs Torque)', 'Position', [200, 200, 700, 600]);
    
    subplot(2,1,1);
    semilogx(omega, mag_dB, 'b-', 'LineWidth', 1.5);
    grid on;
    grid minor;
    ylabel('Magnitude (dB)');
    title('Direct Empirical Bode Plot from Measured Angle & Torque');
    
    subplot(2,1,2);
    semilogx(omega, phase_deg, 'r-', 'LineWidth', 1.5);
    grid on;
    grid minor;
    xlabel('Frequency (rad/s)');
    ylabel('Phase (deg)');
    
    disp('Direct non-parametric Bode plot generated successfully from raw measurements.');
else
    disp('Not enough data collected to generate a reliable direct Bode plot.');
end
Here is a list of all namespace members with links to the namespace documentation for each member:
- a -

    AccCalibrateFinish() : moza
    AccCalibrateStrat() : moza

- b -

    BrakeCalibrateFinish() : moza
    BrakeCalibrateStrat() : moza

- c -

    CenterWheel() : moza
    ClutchCalibrateFinish() : moza
    ClutchCalibrateStrat() : moza
    createWheelbaseETConstantForce() : moza
    createWheelbaseETDamper() : moza
    createWheelbaseETFriction() : moza
    createWheelbaseETInertia() : moza
    createWheelbaseETSine() : moza
    createWheelbaseETSpring() : moza
    CruiseCancel : moza
    CruiseDecrease : moza
    CruiseIncrease : moza
    CruiseOnOff : moza

- d -

    DI_MSECONDS : RS21::direct_input

- e -

    enumHidDevices() : MozaPriv
    enumShifterDevices() : moza
    enumSwitchesDevices() : moza

- f -

    Flasher : moza
    FlasherOff : moza
    FogLight : moza
    FrontWiperHigh : moza
    FrontWiperInterval : moza
    FrontWiperLow : moza
    FrontWiperOff : moza
    FrontWiperSingle : moza
    FrontWiperWash : moza

- g -

    getDeviceParent() : moza
    getDisplayScreenScreenBrightness() : moza
    getDisplayScreenScreenCurrentUI() : moza
    getDisplayScreenScreenUIList() : moza
    getDisplayScreenSpeedUnit() : moza
    getDisplayScreenTemperatureUnit() : moza
    getHandbrakeApplicationMode() : moza
    getHandbrakeNonLinear() : moza
    getHandbrakeOutDir() : moza
    getHandingShifterAutoBlipDuration() : moza
    getHandingShifterAutoBlipOutput() : moza
    getHandingShifterAutoBlipSwitch() : moza
    getHIDData() : moza
    getMotorEqualizerAmp() : moza
    getMotorFfbReverse() : moza
    getMotorFfbStrength() : moza
    getMotorHandsOffProtection() : moza
    getMotorLimitAngle() : moza
    getMotorLimitWheelSpeed() : moza
    getMotorNaturalDamper() : moza
    getMotorNaturalFriction() : moza
    getMotorNaturalInertia() : moza
    getMotorNaturalInertiaRatio() : moza
    getMotorPeakTorque() : moza
    getMotorRoadSensitivity() : moza
    getMotorSpeedDamping() : moza
    getMotorSpeedDampingStartPoint() : moza
    getMotorSpringStrength() : moza
    getPedalAccNonLinear() : moza
    getPedalAccOutDir() : moza
    getPedalBrakeNonLinear() : moza
    getPedalBrakeOutDir() : moza
    getPedalBrakePressCombine() : moza
    getPedalClutchNonLinear() : moza
    getPedalClutchOutDir() : moza
    getSteeringWheelClutchPaddleAxisMode() : moza
    getSteeringWheelClutchPaddleCombinePos() : moza
    getSteeringWheelJoystickHatswitchMode() : moza
    getSteeringWheelKnobMode() : moza
    getSteeringWheelScreenBrightness() : moza
    getSteeringWheelScreenCurrentUI() : moza
    getSteeringWheelScreenUIList() : moza
    getSteeringWheelShiftIndicatorBrightness() : moza
    getSteeringWheelShiftIndicatorColor() : moza
    getSteeringWheelShiftIndicatorLightRpm() : moza
    getSteeringWheelShiftIndicatorMode() : moza
    getSteeringWheelShiftIndicatorSwitch() : moza
    getSteeringWheelSpeedUnit() : moza
    getSteeringWheelTemperatureUnit() : moza
    getSwitchesDeviceState() : MozaPriv

- h -

    HandbrakeCalibrateFinish() : moza
    HandbrakeCalibrateStart() : moza
    HeadlightHigh : moza
    HeadlightOff : moza
    HeadlightPark : moza
    HighBeam : moza

- i -

    installMozaSDK() : moza

- m -

    MAX_SWITCHES_INDEX : moza
    motorMoveTo() : moza
    motorStopMove() : moza

- r -

    RearWiperOff : moza
    RearWiperSpray : moza
    RearWiperWash : moza
    removeMozaSDK() : moza

- s -

    setDisplayScreenScreenBrightness() : moza
    setDisplayScreenScreenCurrentUI() : moza
    setDisplayScreenSpeedUnit() : moza
    setDisplayScreenTemperatureUnit() : moza
    setHandbrakeApplicationMode() : moza
    setHandbrakeNonLinear() : moza
    setHandbrakeOutDir() : moza
    setHandingShifterAutoBlipDuration() : moza
    setHandingShifterAutoBlipOutput() : moza
    setHandingShifterAutoBlipSwitch() : moza
    setMotorEqualizerAmp() : moza
    setMotorFfbReverse() : moza
    setMotorFfbStrength() : moza
    setMotorHandsOffProtection() : moza
    setMotorLimitAngle() : moza
    setMotorLimitWheelSpeed() : moza
    setMotorNaturalDamper() : moza
    setMotorNaturalFriction() : moza
    setMotorNaturalInertia() : moza
    setMotorNaturalInertiaRatio() : moza
    setMotorPeakTorque() : moza
    setMotorRoadSensitivity() : moza
    setMotorSpeedDamping() : moza
    setMotorSpeedDampingStartPoint() : moza
    setMotorSpringStrength() : moza
    setPedalAccNonLinear() : moza
    setPedalAccOutDir() : moza
    setPedalBrakeNonLinear() : moza
    setPedalBrakeOutDir() : moza
    setPedalBrakePressCombine() : moza
    setPedalClutchNonLinear() : moza
    setPedalClutchOutDir() : moza
    setSteeringWheelClutchPaddleAxisMode() : moza
    setSteeringWheelClutchPaddleCombinePos() : moza
    setSteeringWheelJoystickHatswitchMode() : moza
    setSteeringWheelKnobMode() : moza
    setSteeringWheelScreenBrightness() : moza
    setSteeringWheelScreenCurrentUI() : moza
    setSteeringWheelShiftIndicatorBrightness() : moza
    setSteeringWheelShiftIndicatorColor() : moza
    setSteeringWheelShiftIndicatorLightRpm() : moza
    setSteeringWheelShiftIndicatorMode() : moza
    setSteeringWheelShiftIndicatorSwitch() : moza
    setSteeringWheelSpeedUnit() : moza
    setSteeringWheelTemperatureUnit() : moza
    ShifterCalibrateFinish() : moza
    ShifterCalibrateStart() : moza
    SoftReboot() : moza
    stopForceFeedback() : moza
    SwitchesIndex : moza

- t -

    TurnLeft : moza
    TurnRight : moza
    TurnSignalOff : moza

- w -

    WiperSensitivity1 : moza
    WiperSensitivity2 : moza
    WiperSensitivity3 : moza
    WiperSensitivity4 : moza
    WiperSensitivity5 : moza

