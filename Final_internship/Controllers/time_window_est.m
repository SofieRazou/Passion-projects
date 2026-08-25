function time_win = time_window_est(E)
persistent t_prev;

if isempty(t_prev)
    t_prev = 0.001;
end 

kappa = 1;
ZCR_energy = zerocrossrate(E);
time_win = kappa*t_prev + ZCR_energy;


end 
