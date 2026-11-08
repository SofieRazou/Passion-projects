%Fetching urdf of robot arm 
[robot, importInfo] = importrobot('my_robo');
exportrobot(robot, ...
    OutputFileName="my_robo.urdf", ...
    ExportMesh=false);

%Copy urdf file to controller ros2 directory
copyfile('my_robo.urdf', '/Users/sofia/ws2/src/robo_arm/src/robo_description/urdf/my_robo.urdf');