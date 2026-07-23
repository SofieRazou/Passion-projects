function [scenario, egoVehicle] = drive1(waypoints, u)

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

end
