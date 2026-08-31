This repo includes the code, control models and results I got from my 2-month internship at the Haptics Intelligence Department, at the Max Planck Institute for Intelligent Systems in Stuttgart, on the "Continuous and Precise Torque Motor (CAPT)" Project. 

The code is logically organised in the following categories:
- The GUI-related code, which was used to build the front-end and back-end of the CAPT Motor dashboard, with UDP communication and a shared-memory architecture between the communicating modules. It also includes the MATLAB and Simulink codes for the driving simulation.

- The Controller modules where the impedance, energy based controllers and the tested with inertia and damping models are included.
- The Moza-related code to establish communication eiyh the Moza Software Development Kit (SDK) which allows for more enhanced and customisable haptic force feedback effects, angle, velocity anf acceleration fetching.
- Results: figures and data from system id and controller performance and the motor's haptic fidelity via the relative Bode plots. 
