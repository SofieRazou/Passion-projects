---
title: System Identification Logic and Workflow 
description: This document outlines the step-by-step logic used to perform grey-box system identification and model approximation for the CAPT motor using experimental distance and load data[cite: 3].  
---

## Data Preparation and Preprocessing
1. **Loading Experimental Sets:** The script loads raw trial data from exp_distance.mat, mapping time vectors, angles and torque streams across multiple experimental runs[cite: 3].  

2. **Filtering and Scaling:** An 8th-order low-pass Butterworth filter ($f_c = 20\text{ Hz}$) is applied to smooth out high-frequency noise in the torque load measurements[cite: 3]. Preload offsets for both torque sent and torque load are computed and subtracted[cite: 3].  

3. **Segment Extraction:** The script programmatically detects period rising edges using gradient thresholds to isolate stable 5-period operational windows from the continuous test data[cite: 3].  

## Parameter Estimation & Grey-Box Modeling
* **Fixed Inertia Constraint:** Knowing the physical motor construction, the system inertia is fixed at $J = 0.0103$[cite: 3].  

* **Transfer Function Structure:** The system is modeled as a second-order spring-mass-damper system using the transfer function:
  $$G(s) = \frac{1}{J s^2 + b s + k}$$[cite: 3]
 
* **Parameter Initialization:** Initial estimations for damping ($b \approx 9.0$) and stiffness ($k \approx 42.0$) are provided to guide the optimization solver toward the physical operating range of the hardware[cite: 3].  

* **Model Fitting:** Both a Transfer Function (Gest) and a State-Space model (Gss) are fitted against the identification dataset (iddata) using backcast initial conditions and optimized via Root Mean Square Error (RMSE) minimization[cite: 3].  

## Validation and Visualization
* **Time-Domain Comparison:** Plots measured tracking data (data_id) against simulated model outputs (Gest and Gss), reporting individual percentage fit metrics[cite: 3].  

* **Frequency-Domain Analysis:** Generates Bode response plots to evaluate system dynamics, resonance peaks, and phase behavior across operating points[cite: 3].