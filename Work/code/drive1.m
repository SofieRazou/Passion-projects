(* function [scenario, egoVehicle] = drive1(waypoints, u)

%% Create scenario
scenario = drivingScenario;

%% Road
roadCenters = [ ...
    55.8 5.9 0;
    42.4 16.4 0;
    37.3 18.3 0;
    28.1 25.6 0;
    20.3 17.9 0;
    18.7 -5.3 0;
    14.6 10.6 0;
    4.6 12.8 0;
    2.2 21.3 0;
   -1.8 30.2 0;
   -4.8 17.9 0;
   -4.9 5.5 0;
    1.6 -4.4 0;
   10.8 -7.1 0;
   14.9 -13.1 0;
   26.0 -16.8 0;
   42.7 -31.8 0;
   51.1 -10.1 0;
   53.4 -3.3 0;
   55.8 5.9 0];

road(scenario, roadCenters);

%% Ego vehicle
egoVehicle = vehicle( ...
    scenario, ...
    'ClassID',1, ...
    'Position', waypoints(1,:));

%% Assign trajectory
trajectory(egoVehicle, waypoints, u);

%% Visualize
figure('Name','Driving Scenario');

plot(scenario,...
    'Waypoints','on',...
    'RoadCenters','on');

restart(scenario);

%% Run the simulation
while advance(scenario)
    drawnow;
end

end *)

clear;
clc;
close all;

%% Configuration
Ts = 0.01;                 % 100 Hz simulation/update rate
simulationDuration = 30;   % seconds

%% Create scenario and ego vehicle
[scenario, egoVehicle] = drive1();

%% Open driving scenario viewer
viewer = drivingScenarioViewer( ...
    scenario, ...
    "ShowRoadBoundaries", true, ...
    "ShowLaneMarkings", true, ...
    "ShowActorMeshes", true, ...
    "ShowWaypoints", false);

%% Initial vehicle state
x = egoVehicle.Position(1);
y = egoVehicle.Position(2);
yaw = deg2rad(egoVehicle.Yaw);

wheelbase = 1.0;   % metres
speed = 10.0;      % m/s

%% Store generated trajectory
maxSamples = ceil(simulationDuration / Ts) + 1;

generatedTrajectory = zeros(maxSamples, 4);
% Columns: time, x, y, yaw

sampleIndex = 1;

%% Real-time loop
startTime = tic;
nextUpdateTime = 0;

while toc(startTime) < simulationDuration

    currentTime = toc(startTime);

    % Wait until the next real-time update
    if currentTime < nextUpdateTime
        pause(nextUpdateTime - currentTime);
    end

    currentTime = toc(startTime);

    %% Read steering command
    % Replace this example with your shared-memory or UDP steering value.
    steeringAngle = deg2rad(10) * sin(0.4 * currentTime);

    %% Bicycle model
    yawRate = speed / wheelbase * tan(steeringAngle);

    yaw = yaw + yawRate * Ts;

    x = x + speed * cos(yaw) * Ts;
    y = y + speed * sin(yaw) * Ts;

    %% Update ego vehicle
    egoVehicle.Position = [x, y, 0];
    egoVehicle.Yaw = rad2deg(yaw);
    egoVehicle.Velocity = ...
        [speed * cos(yaw), speed * sin(yaw), 0];
    egoVehicle.AngularVelocity = [0, 0, yawRate];

    %% Save generated point
    generatedTrajectory(sampleIndex, :) = ...
        [currentTime, x, y, yaw];

    sampleIndex = sampleIndex + 1;

    %% Refresh scenario viewer
    updatePlots(viewer);
    drawnow limitrate;

    nextUpdateTime = nextUpdateTime + Ts;
end

%% Remove unused allocated rows
generatedTrajectory = ...
    generatedTrajectory(1:sampleIndex - 1, :);

disp("Driving simulation finished.");
