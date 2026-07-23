%% ============================================================
% Inject workspace trajectory into an existing scenario MAT file
% =============================================================

scenarioMatFile = ...
    "C:\Users\javot\Desktop\sofia_code\existingScenario.mat";

outputMatFile = ...
    "C:\Users\javot\Desktop\sofia_code\scenario_with_trajectory.mat";

vehicleSpeed = 30.0;     % m/s
egoActorIndex = 1;       % Change if the ego vehicle is not actor 1

%% Check that the trajectory exists in the workspace

if ~exist("generatedWaypoints", "var")
    error( ...
        "generatedWaypoints does not exist in the MATLAB workspace.");
end

waypoints = double(generatedWaypoints);

%% Accept either [x y] or [x y z]

if size(waypoints, 2) == 2
    waypoints(:, 3) = 0;
elseif size(waypoints, 2) ~= 3
    error( ...
        "generatedWaypoints must be an N-by-2 or N-by-3 array.");
end

%% Remove invalid points

validRows = all(isfinite(waypoints), 2);
waypoints = waypoints(validRows, :);

%% Remove consecutive duplicate points

if size(waypoints, 1) > 1
    pointChange = [ ...
        true; ...
        any(abs(diff(waypoints, 1, 1)) > 1e-9, 2) ...
    ];

    waypoints = waypoints(pointChange, :);
end

if size(waypoints, 1) < 2
    error( ...
        "At least two different trajectory points are required.");
end

%% Load every variable from the existing MAT file

if ~isfile(scenarioMatFile)
    error("Scenario MAT file not found:\n%s", scenarioMatFile);
end

scenarioData = load(scenarioMatFile);

%% Find the drivingScenario object automatically

fieldNames = fieldnames(scenarioData);
scenarioField = "";

for k = 1:numel(fieldNames)

    candidate = scenarioData.(fieldNames{k});

    if isa(candidate, "drivingScenario")
        scenarioField = string(fieldNames{k});
        break;
    end
end

if scenarioField == ""
    error( ...
        ["The MAT file does not contain a drivingScenario object. " ...
         "Export the scenario as a MATLAB function instead of only " ...
         "saving the Driving Scenario Designer session."]);
end

scenario = scenarioData.(scenarioField);

%% Get actors from the scenario

actors = scenario.Actors;

if isempty(actors)
    error("The scenario does not contain any actors.");
end

if egoActorIndex < 1 || egoActorIndex > numel(actors)
    error( ...
        "egoActorIndex must be between 1 and %d.", ...
        numel(actors));
end

egoCar = actors(egoActorIndex);

fprintf( ...
    "Using actor %d of %d as the ego vehicle.\n", ...
    egoActorIndex, ...
    numel(actors));

%% Reset the scenario before replacing the actor trajectory

restart(scenario);

%% Assign workspace trajectory to the existing actor

trajectory( ...
    egoCar, ...
    waypoints, ...
    vehicleSpeed);

%% Calculate a suitable scenario duration

segmentLengths = vecnorm(diff(waypoints(:, 1:2), 1, 1), 2, 2);
totalDistance = sum(segmentLengths);

estimatedDuration = totalDistance / vehicleSpeed;

scenario.StopTime = max( ...
    scenario.SampleTime, ...
    estimatedDuration);

%% Put the modified scenario back into the loaded structure

scenarioData.(scenarioField) = scenario;

%% Save all original MAT variables plus the injected trajectory

scenarioData.importedWaypoints = waypoints;
scenarioData.importedVehicleSpeed = vehicleSpeed;
scenarioData.egoActorIndex = egoActorIndex;

save( ...
    outputMatFile, ...
    "-struct", ...
    "scenarioData");

fprintf("\nTrajectory successfully injected.\n");
fprintf("Waypoints: %d\n", size(waypoints, 1));
fprintf("Distance: %.2f m\n", totalDistance);
fprintf("Estimated duration: %.2f s\n", estimatedDuration);
fprintf("Saved as:\n%s\n", outputMatFile);

%% Optional preview

restart(scenario);

figure( ...
    "Name", "Scenario With Imported Trajectory", ...
    "NumberTitle", "off");

plot( ...
    scenario, ...
    "Waypoints", "on", ...
    "RoadCenters", "on");

while advance(scenario)
    pause(scenario.SampleTime);
end
