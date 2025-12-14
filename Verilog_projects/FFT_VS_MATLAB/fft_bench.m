%% FFT Test in MATLAB

clc; clear; close all;
N = 8;
x_r = [2147483647, 1518500249, 0, -1518500249, -2147483647, -1518500249, 0, 1518500249];
x_i = [0, 1518500249, 2147483647, 1518500249, 0, -1518500249, -2147483647, -1518500249];
x = double(x_r) + 1j*double(x_i);

tic  % Start timing
X = fft(x);
elapsed_time = toc;  % Stop timing and store result

fprintf('FFT runtime: %.6f seconds\n', elapsed_time);

% Optional: Plot magnitude and phase
figure;
subplot(2,1,1);
stem(0:N-1, abs(X));
title('FFT Magnitude');
xlabel('k'); ylabel('|X[k]|');
grid on;

subplot(2,1,2);
stem(0:N-1, angle(X));
title('FFT Phase');
xlabel('k'); ylabel('Angle (radians)');
grid on;
