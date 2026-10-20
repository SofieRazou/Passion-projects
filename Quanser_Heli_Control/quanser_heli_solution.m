%%-------MIT 31 Lab 16.30 #1------------
clear; clc;

% 1. Define Numerical Parameters (from Table 1)
m = 1.15;           % Mass of rotor assembly (kg)[cite: 2]
M = 3.57;           % Mass of whole setup (kg)[cite: 2]
l_boom = 0.66;      % Length from pivot point to heli body (m)[cite: 2]
l_phi = 0.004;      % Length of pendulum for roll axis (m)[cite: 2]
l_theta = 0.014;    % Length of pendulum for pitch axis (m)[cite: 2]
l_h = 0.177;        % Length from pivot point to the rotor (m)[cite: 2]
I_xx = 0.036;       % Moment of inertia about x-axis (Nm)[cite: 2]
I_yy = 0.93;        % Moment of inertia about y-axis (Nm)[cite: 2]
I_zz = 0.93;        % Moment of inertia about z-axis (approximation/placeholder)
K_tau = 4.25*10^-3; % Coefficient of thrust (N/s)[cite: 2]
theta_rest = deg2rad(-25); % Theta rest value converted to radians[cite: 2]
g = 9.81;           % Acceleration due to gravity (m/s^2)[cite: 2]
L_p = 0.2;          % Max roll damping coefficient (middle of [0.02, 0.2] range)[cite: 2, 4]
M_q = 0.9;          % Max pitch damping coefficient (middle of [0.1, 0.9] range)[cite: 2, 4]
K_D = 0.01;         % Induced drag coefficient (placeholder)
K_v = 0.01;         % Velocity coupling coefficient (placeholder)

% 2. Declare Symbolic Variables for States and Inputs
syms phi dphi theta dtheta psi dpsi w_cyc w_coll real
syms V_cyc V_coll real
% 3. Define Auxiliary Forces and Motor Dynamics (Eqs. 4-8)[cite: 2]
D = K_D * dpsi;
tau_coll = K_tau * w_coll - K_v * dpsi;
tau_cyc = K_tau * w_cyc - K_v * psi;

dw_cyc = 780 * V_cyc - 6 * w_cyc;
dw_coll = 540 * V_coll - 6 * w_coll;

% 4. Define Accelerations from Equations of Motion (Eqs. 1-3)
% (Assuming omega_rotor = 0 and gamma = 0 for the pre-lab transfer functions)[cite: 3, 4]
omega_rotor = 0;
gamma = 0;

ddphi = (tau_cyc * l_h - m * g * l_phi * sin(phi) - L_p * dphi) / I_xx;
ddtheta = (tau_coll * l_boom * cos(phi) - M * g * l_theta * sin(theta + theta_rest) - ...
           D * l_boom * sin(gamma) - M_q * dtheta) / I_yy;
ddpsi = (tau_coll * l_boom * sin(phi) - D * l_boom * cos(gamma)) / I_zz;

% 5. Construct State Vector (8 states) and Input Vector (2 inputs)
x = [phi; dphi; theta; dtheta; psi; dpsi; w_cyc; w_coll];
f = [dphi; ddphi; dtheta; ddtheta; dpsi; ddpsi; dw_cyc; dw_coll];
u = [V_cyc; V_coll];

% 6. Compute Symbolic Jacobians
A_sym = jacobian(f, x);
B_sym = jacobian(f, u);

% 7. Define Operating Point and Evaluate Jacobians Numerically
x_op = zeros(8, 1);
u_op = zeros(2, 1);

% Substitute the operating point into the symbolic matrices
A = double(subs(A_sym, [x; u], [x_op; u_op]));
B = double(subs(B_sym, [x; u], [x_op; u_op]));

disp('Evaluated A matrix:');
disp(A);
disp('Evaluated B matrix:');
disp(B);

C = [1 0 0 0 0 0 0 0];
D = [0];
heli_sys = ss(A,B,C,D);

C_roll  = [1, 0, 0, 0, 0, 0, 0, 0]; 
C_pitch = [0, 0, 1, 0, 0, 0, 0, 0]; 

sys_roll  = ss(A, B(:, 1), C_roll, 0);
sys_pitch = ss(A, B(:, 2), C_pitch, 0);

%Uncomment to reveal the system designer for control of the two angles to
%reach the targeted reference, each 
% controlSystemDesigner(sys_roll);
% controlSystemDesigner(sys_pitch);

%Mcoll and Mcyc transfer functions
Mcoll = tf([540], [1 4]);
Mcyc = tf([780], [1 6]);

figure;
step(Mcoll, "cyan");
title("Collective Motor step response");
grid on;
hold on;

figure;
step(Mcyc, "magenta");
title("Cyclic Motor step response");
grid on;

%QP and QR transfer functions

QP = tf([0.0030], [1 0.4778, 0.5376]);
QR = tf([0.209], [1 1.2535 2.778]);

figure;
step(QP, "yellow");
title("Pitch system tf step response");
grid on;
hold on;

step(QR, "blue");
title("Roll system tf step response");
grid on;

%%Controller development for roll and pitch axes
Lp = 0.11; %half of nominal value 
Mq = 0.4; %half of nominal value


%CP transfer function
CP = tf([2.4732 4.122 1.7175], [1 0]);
Kd_p =2.4732;
Kp_p = 4.122;
Ki_p =1.7175;

TP = (Mcoll*QP*CP)/(1+Mcoll*QP*CP);
[num_p, den_p]= tfdata(TP,'v');


[Ap, Bp, Cp, Dp] = tf2ss(num_p, den_p);
sys_pitch_controlled = ss(Ap, Bp, Cp, Dp);
Ctrb_p = ctrb(sys_pitch_controlled);

if rank(Ap)== rank(Ctrb_p)
    disp("System of helicopter controllable, by pitch");
end

figure;
bode(CP, "yellow");
title("Pitch controller bode diagramme");
grid on;
hold on;

%CR transfer function 
CR = tf([0.8578 2.0957 0.9747], 1);
Kd_r =  0.8578; 
Kp_r = 2.0957;
Ki_r =  0.9747;

TR = (Mcyc*QR*CR)/(1+Mcyc*QR*CR);
[num_r, den_r]= tfdata(TR,'v');


[Ar, Br, Cr, Dr] = tf2ss(num_r, den_r);
sys_roll_controlled = ss(Ar, Br, Cr, Dr);
Ctrb_r = ctrb(sys_roll_controlled);

if rank(Ar)== rank(Ctrb_r)
    disp("System of helicopter controllable, by roll");
end


bode(CR, "blue");
title("Roll controller bode diagramme");
grid on;




