function kappa = estimate_torsional_stiffness(torque_data, theta_data, zero_offset)
% ESTIMATE_TORSIONAL_STIFFNESS Calculates kappa using least-squares regression.
%
% Inputs:
%   torque_data - Logged raw torque vector or load cell values
%   theta_data  - Logged angular position vector from the encoder (rad)
%   zero_offset - Optional load cell zero/tare offset (if empty, it auto-calculates from start)
%
% Output:
%   kappa       - Estimated rotational stiffness (N*m/rad)

    % Ensure column vectors
    torque_data = torque_data(:);
    theta_data = theta_data(:);
    
    % Handle load cell zero offset
    if nargin < 3 || isempty(zero_offset)
        % Default: average the first 50 samples at rest as the offset
        zero_offset = mean(torque_data(1:min(50, length(torque_data))));
    end
    
    % Correct torque with zero offset
    tau_actual = torque_data - zero_offset;
    
    % Compute stiffness using linear least-squares (tau = kappa * theta)
    % Formula minimizes error: kappa = sum(tau .* theta) / sum(theta .^ 2)
    denominator = sum(theta_data .^ 2);
    
    if denominator == 0
        error('Theta data is all zeros; cannot compute stiffness.');
    end
    
    kappa = sum(tau_actual .* theta_data) / denominator;
    
    % Display results for feedback
    fprintf('--- Torsional Stiffness Estimation ---\n');
    fprintf('Estimated Kappa: %.4f N*m/rad\n', kappa);
end
