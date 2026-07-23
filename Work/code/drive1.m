function [scenario, egoVehicle] = drive1(waypoints, u)

%% Validate inputs
if nargin < 2
    error('Call the function as drive1(waypoints, u).');
end

if size(waypoints, 2) == 2
    % Add a zero Z-coordinate
    waypoints(:, 3) = 0;
elseif size(waypoints, 2) ~= 3
    error('waypoints must be an N-by-2 or N-by-3 matrix.');
end

if size(waypoints, 1) < 2
    error('At least two waypoints are required.');
end

%% Create scenario
scenario = drivingScenario( ...
    'SampleTime', 0.01);

%% Road
roadCenters = [ ...
    55.8   5.9   0;
    42.4  16.4   0;
    37.3  18.3   0;
    28.1  25.6   0;
    20.3  17.9   0;
    18.7  -5.3   0;
    14.6  10.6   0;
     4.6  12.8   0;
     2.2  21.3   0;
    -1.8  30.2   0;
    -4.8  17.9   0;
    -4.9   5.5   0;
     1.6  -4.4   0;
    10.8  -7.1   0;
    14.9 -13.1   0;
    26.0 -16.8   0;
    42.7 -31.8   0;
    51.1 -10.1   0;
    53.4  -3.3   0;
    55.8   5.9   0];

road(scenario, roadCenters);

%% Ego vehicle
egoVehicle = vehicle( ...
    scenario, ...
    'ClassID', 1, ...
    'Position', waypoints(1, :), ...
    'Name', 'Ego Vehicle');

%% Assign complete predefined trajectory
trajectory(egoVehicle, waypoints, u);

%% Top-down scenario view
figure( ...
    'Name', 'Driving Scenario', ...
    'NumberTitle', 'off');

plot( ...
    scenario, ...
    'Waypoints', 'on', ...
    'RoadCenters', 'on');

%% Ego-centric perspective view
figure( ...
    'Name', 'Ego Vehicle View', ...
    'NumberTitle', 'off');

chasePlot( ...
    egoVehicle, ...
    'Waypoints', 'on', ...
    'RoadCenters', 'on');

%% Reset scenario to start
restart(scenario);

%% Run simulation
while advance(scenario)
    drawnow limitrate;
end

end
