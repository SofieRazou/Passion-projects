%"Real" physical system dynamics
s = tf('s');
Greal = 5*(s+1)/(s^2 + 6*s + 6.7)*exp(-0.1*s);
Ts = 0.01; %sample time in sec
%Data collection with said input and output tracking
dt = Ts;
t = 0:dt:5;

u = ones(length(t),1);
u(1:1/dt) = 0; %inital condition

yreal = lsim(Greal, u, t);

plot(t, [u, yreal], 'LineWidth', 4);
axis([0 5 0 1.4]);
grid on;
legend(['u';'y']);

%Fit data to said model structure 
data = iddata(yreal, u, dt);
Gest = tfest(data,2, 0, NaN);

%Draw comparison between the dynamics and the fitted model 
opt = compareOptions;
opt.InitialCondition = 'z';
compare(data,Gest,opt);
set(findall(gca, 'Type', 'Line'), 'LineWidth', 4');
grid on;
