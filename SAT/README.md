## SAT Solver for Sensor Fusion  
### Navigation Assistance for Visually Impaired People with Force Feedback

This project combines three major interests of mine (pun intended):  
**hardware–software co-design, formal verification, and assistive healthcare technologies.**

The result is **SAT Fusion**, a lightweight SAT-based decision engine designed for **sensor fusion in embedded systems**.

The system is built around a SAT solver that operates on **CNF (Conjunctive Normal Form)** clauses.  
The original solver was implemented in **C++**, and later optimized to run with **minimal memory and computational resources** for microcontroller-based platforms.

### Sensor Fusion Architecture

The navigation assistance module integrates multiple sensors commonly used for mobility support:

- **IMU (Inertial Measurement Unit)** – detects tumbling or dangerous tilt conditions
- **Ultrasonic Sensor** – identifies dynamic and static obstacles
- **Dual IR Sensors** – enable line-following and path tracking

These sensor signals are converted into logical clauses and evaluated by the SAT-based decision system.

### Haptic Feedback

The system communicates navigation decisions to the user through **force feedback**:

- A **servo motor** provides tactile cues
- Different sensor fusion outcomes produce **distinct feedback responses**
- This allows the user to receive intuitive navigation guidance without visual input

### Goal

The aim of this project is to explore how **formal logic systems such as SAT solvers can be repurposed for real-world embedded applications**, particularly in **assistive technologies for visually impaired individuals**.

Enjoy!

---

![SAT Fusion Diagram](/SAT/project_sat.png)
