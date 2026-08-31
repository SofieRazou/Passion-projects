# Continuous and Precise Torque Motor (CAPT) Project

Welcome to the official repository for my 2-month internship at the **Haptics Intelligence Department** of the **Max Planck Institute for Intelligent Systems** in Stuttgart, Germany. This repository contains the complete code, control models, system identification benchmarks, and experimental results developed for the **Continuous and Precise Torque Motor (CAPT)** project.

---

## Table of Contents
* [About the Project](#-about-the-project)
* [Repository Structure](#-repository-structure)
* [Detailed Module Breakdown](#-detailed-module-breakdown)
  * [1. GUI & Simulation](#1-gui--simulation)
  * [2. Controller Modules](#2-controller-modules)
  * [3. System Identification](#3-system-identification)
  * [4. Moza SDK Integration](#4-moza-sdk-integration)
  * [5. Results & Performance Analysis](#5-results--performance-analysis)
  * [6. Documentation (MkDocs)](#6-documentation-mkdocs)
* [Getting Started](#-getting-started)
* [Acknowledgments](#-acknowledgments)

---

## About the Project

The **Continuous and Precise Torque Motor (CAPT)** project focuses on advancing high-fidelity haptic feedback systems, precision torque control, and robust system modeling. During my internship at the Max Planck Institute for Intelligent Systems, I worked on bridging low-level hardware communication with high-level graphical interfaces, implementing sophisticated control algorithms (such as impedance and energy-based controllers), and benchmarking system performance through rigorous identification techniques.

---

## Repository Structure

The codebase is logically organized into the following primary categories:

```text
Final_internship/
│
├── GUI/                  # Front-end & back-end dashboard, UDP/shared memory, MATLAB/Simulink
├── Controllers/          # Impedance, energy-based controllers, inertia & damping models
├── SYS_ID/               # System identification benchmarks (Transfer functions vs. canonical forms)
├── MOZA/                 # Moza SDK integration for custom force feedback and state fetching
├── results/              # Experimental data, performance figures, and Bode plots
└── my-docs-site/         # Local MkDocs site detailing code architecture and engineering decisions
```

---

## Detailed Module Breakdown

### 1. GUI & Simulation (`/GUI`)
* **Dashboard Architecture:** Implements a robust front-end and back-end for real-time monitoring and control of the CAPT motor.
* **Communication:** Utilizes **UDP communication** alongside a **shared-memory architecture** to ensure low-latency data exchange between concurrent modules.
* **Simulations:** Houses MATLAB and Simulink models used for virtual driving simulations and pre-validation of control strategies.

### 2. Controller Modules (`/Controllers`)
* **Impedance Control:** Regulates the dynamic interaction between the motor and the user/environment.
* **Energy-Based Control:** Guarantees passivity and stability under various operating conditions.
* **Model Testing:** Validates controllers against specific physical phenomena, including variable inertia and damping models.

### 3. System Identification (`/SYS_ID`)
* Dedicated scripts and routines for extracting accurate plant models.
* Benchmarks **transfer function models** against **canonical system form representations** to determine the optimal identification approach for haptic transparency.

### 4. Moza SDK Integration (`/MOZA`)
* Interfaces with the **Moza Software Development Kit (SDK)**.
* Unlocks advanced, highly customizable haptic force-feedback effects.
* Fetches high-frequency telemetry data including precise angle, velocity, and acceleration measurements.

### 5. Results & Performance Analysis (`/results`)
* Contains generated figures and raw experimental data from system identification runs.
* Evaluates tracking and controller performance.
* Highlights motor haptic fidelity via **relative Bode plots** (magnitude and phase responses).

### 6. Documentation (`/my-docs-site`)
* Source files for the local **MkDocs** instance.
* Serves as an extensive engineering wiki detailing API usage, software design patterns, and the rationale behind key engineering decisions.

---

## Getting Started

### Prerequisites
Ensure you have the required software environments installed depending on the module you wish to run:
* **Python** (for GUI backend, UDP handling, and data processing)
* **MATLAB / Simulink** (for simulation and control model development)
* **MkDocs** (optional, if you wish to build and view the local documentation site)

### Running the Documentation Locally
To preview the MkDocs documentation site locally:
```bash
# Install MkDocs (if not already installed)
pip install mkdocs

# Navigate to the docs directory and serve
cd docs
mkdocs serve
```

---

## Acknowledgments
Special thanks to my supervisor Prof. Dr. Katherine J. Kuchenbecker and my mentors Dr. Bernard Javot and Dr. Giulia Ballardini, at the **Haptics Intelligence Department** of the **Max Planck Institute for Intelligent Systems** for their guidance and support throughout this internship.

---
