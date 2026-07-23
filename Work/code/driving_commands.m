
u = 30; %m/s
x_0 = 0.0; %m
y_0 = 0.0; %m
L = 1; %m
time_step = 0.001;
trajectory = {}
while !commands.empty()
    
    trajectory{end+1} = run_driving_venv(
   
    
    
end


outputScenario = exportToDrivingScenario(trajectory);
