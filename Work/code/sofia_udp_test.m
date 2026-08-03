%%CAPT motor model for testing before deployment to dSpace 
clear;

Ts = 0.001; %sampling time in sec
Td = Ts/2; %approx delay period for Pade ZOH approximation 

Gc = tf([-Td/2 1], [Td/2 1]);
Gd = c2d(Gc,Ts,'tustin');
[num_d, den_d] = tfdata(Gd, 'v');


%Plant model parameters 
J_virtual = 0.002; %virtual inertia
J_inherit = 0.0103; % actual mass moment of inertia of the motor's 
J = J_virtual + J_inherit; % total rendered inertia of the motor's
k = 0.1; %virtual stiffness
b = 0.05;%virtual damping 
theta_ref=0;
omega_c = 62; %in rads/sec (natural median freq)
omega_d = 2*pi*100;

%Linear Motor state-space model 
A = [0 1; -k/J -b/J];
B =[0; 1/J];
C=[1 0];
D=zeros();

sys = ss(A,B,C,D);

cm = ctrb(sys);
obsm = obsv(sys);
if rank(cm)==rank(A)
    disp("Plant is controllable");
else
    disp("Plant is non-controllable");
end

if rank(obsm)==rank(A)
    disp("Plant is observable");
else
    disp("Plant is non-observable");
end
eigs = eig(A);
disp(eigs);

figure;
bode(sys);
grid on;
saveas(gcf, "C:\Users\javot\Desktop\sofia_code\bode_plot.png");

%writeouts for gui for stability analysis 
[A,B,C,D] = ssdata(sys);
save('plant_matrixes.mat','A','B','C', 'D');

esp_0 = 0.01; 

%Linear Human state-space model parameters
%-- init --
kh = 1;
Mh = 1;
bh = 1;

%Human impedance transfer function for human-device system charactiri
%--state-space --
Ah = [0 1; -kh/Mh -bh/Mh];
Bh =[0; 1/Mh];
Ch=[1 0];
Dh=zeros();
human_0 = ss(Ah,Bh,Ch,Dh);
cm_human_0 = ctrb(human_0);
obsm_human_0 = obsv(human_0);
if rank(cm_human_0)==rank(Ah)
    disp("Init Human is controllable");
else
    disp("Init Human is non-controllable");
end

if rank(obsm_human_0)==rank(Ah)
    disp("Init Human is observable");
else
    disp("Init Human is non-observable");
end
eigs_human_0 = eig(Ah);
disp(eigs_human_0);

figure;
bode(human_0);
grid on;
saveas(gcf, "C:\Users\javot\Desktop\sofia_code\zero_human_bode_plot.png");

Th = 0.1;
%Estimation of human operator's parameters
%fetch values from simulink to common workspace 
AH = [0 1; -kh/Mh -bh/Mh];
BH = [0; 1/Mh];
CH = [0 1];
DH = zeros();
%Energy control feedback parameters
deltaT = 0.001;
simOut = sim('controller1_SR', ...
    'ReturnWorkspaceOutputs', 'on'); 
%as timeseries
angle_d = simOut.angle;
torque_d = simOut.torque;
tw_d = simOut.tw;

t = angle_d.Time; %simulation time logs
angle = squeeze(angle_d.Data);
torque = squeeze(torque_d.Data);
tw = squeeze(tw_d.Data);

angle = angle(:);
torque = torque(:);
tw = tw(:);

data = iddata(angle, torque, Th);
data.InputName = 'Torque (Nm)';
data.OutputName = 'Angle (deg)';

init_params = {
    'Mh', Mh;
    'bh', bh;
    'kh', kh;
   };

human_zero = idgrey(...
    'human_init_model', ...
    init_params, ...
    'c');

human = greyest(data, human_zero);

%parameter update 
[AH, BH, CH, DH] = ssdata(human);

% Ensure ordinary  matrices
AH = double(AH);
BH = double(BH);
CH = double(CH);
DH = double(DH);

% Make variables available to model 
assignin('base', 'AH', AH);
assignin('base', 'BH', BH);
assignin('base', 'CH', CH);
assignin('base', 'DH', DH);

humanBlock = 'controller1_SR/Human_state_space';

set_param(humanBlock, ...
    'A', 'AH', ...
    'B', 'BH', ...
    'C', 'CH', ...
    'D', 'DH');

set_param('controller1_SR', 'SimulationCommand', 'update');


%check human operator's estimated model stability and observability
cm_human = ctrb(human);
obsm_human = obsv(human);
if rank(cm_human)==rank(AH)
    disp("Init Human is controllable");
else
    disp("Init Human is non-controllable");
end

if rank(obsm_human)==rank(AH)
    disp(" Human is observable");
else
    disp("Human is non-observable");
end
eigs_human = eig(AH);
disp(eigs_human);

figure;
bode(human);
grid on;
saveas(gcf, "C:\Users\javot\Desktop\sofia_code\human_bode_plot.png");

%Evaluate Estimation

mse = human.Report.Fit.MSE;
disp(sqrt(mse));

