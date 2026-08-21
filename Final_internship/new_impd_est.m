% 1. Extract data from Simulink timeseries objects
% (Assuming format was set to Timeseries)
t = torque_data.Time;
tau = torque_data.Data;
theta = theta_data.Data;

% 2. Clean or filter data if necessary (optional moving average or low-pass)
% tau_filtered = smoothdata(tau);
% theta_filtered = smoothdata(theta);

% 3. Calculate rotational stiffness (kappa) using least squares: tau = kappa * theta
% Formula: kappa = sum(tau .* theta) / sum(theta .^ 2)
kappa = sum(tau .* theta) / sum(theta .^ 2);
fprintf('Estimated Torsional Stiffness (kappa): %.4f N*m/rad\n', kappa);

% 4. Plot measured data vs. the fitted stiffness model
figure;
plot(theta, tau, 'b.', 'DisplayName', 'Measured Data');
hold on;
theta_fit = linspace(min(theta), max(theta), 100);
tau_fit = kappa * theta_fit;
plot(theta_fit, tau_fit, 'r-', 'LineWidth', 2, 'DisplayName', sprintf('Fit: \\kappa = %.2f', kappa));
xlabel('Angular Displacement \theta (rad)');
ylabel('Torque \tau (N\cdot m)');
legend('Location', 'northwest');
grid on;
title('Rotational Stiffness Estimation');
