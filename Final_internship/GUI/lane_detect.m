function fcn(X, Y, yaw)
    % Declare persistent variables to hold the plot and plotter objects
    persistent bep olPlotter lbPlotter
    
    % Initialize on the first time step
    if isempty(bep)
        % Create the Bird's-Eye Plot figure window
        bep = birdsEyePlot('XLimits', [-10 50], 'YLimits', [-20 20]);
        
        % Create the outline plotter for the car
        olPlotter = outlinePlotter(bep);
        
        % Create the lane boundary plotter
        lbPlotter = laneBoundaryPlotter(bep);
    end
    
    % Define car dimensions (length, width in meters)
    carLength = 4.7;
    carWidth = 1.8;
    
    % Define the ego vehicle position and orientation [x, y, yaw, length, width, origin_offset]
    % Note: Orientation expects yaw angle in radians
    pose = [X, Y, yaw, carLength, carWidth, 0, 0];
    
    % Update the car outline on the plot
    plotOutline(olPlotter, pose);
    
    % Optional: Add dummy or actual lane boundary coordinates if available
    % and update via lbPlotter using plotLaneBoundary(...)
end
