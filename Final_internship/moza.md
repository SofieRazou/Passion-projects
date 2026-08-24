---
title: Moza R5 Integration
description: Hardware specification, Pygame axis mapping, and haptic feedback integration for the Moza R5 steering wheel system in the CAPT Motor dashboard.
---

# Moza R5 Integration Hub

<div class="grid cards" markdown>

-   **Direct Drive Feedback**

    ---

    Delivers high-fidelity haptic feedback and real-time resistance torque mapped directly from virtual driving simulations.

-   **Pygame Axis Mapping**

    ---

    Polls steering angle, accelerator, and brake inputs using low-latency asynchronous event loops within PyQt6.

-   **Hardware Handshake**

    ---

    Establishes bi-directional communication between host control scripts and physical motor peripherals.

</div>

---

## Hardware & Peripheral Specifications

To ensure seamless integration between the Moza R5 base and the CAPT Motor dashboard, configure your controller parameters according to the operational profile below.

| Configuration Parameter | Target Value | Operational Description |
| :--- | :--- | :--- |
| **`DEVICE_ID`** | `Moza R5 Base` | Recognized USB HID controller interface identifier. |
| **`POLLING_RATE`** | `100 Hz` | Dedicated event loop frequency for joystick axis and button polling. |
| **`MAX_TORQUE_SCALE`** | `5.5 Nm` | Maximum force feedback scaling factor applied to the steering column. |
| **`AXIS_MAPPING`** | `Axis 0 (Steering)` | Primary analog input mapped to virtual road curvature calculations. |

---

### Useful commands for real-time Moza R5 data extraction

For the acquisition of live angle and torque (most importantly) values from the Moza R5 wheel the `pygame` package is used, taking advantage of the USB connection between the wheel and the lab computer.
Some of the most useful commands, include the following:

#### For library initialization
* `pygame.init` : Triggers packet setup
* `pygame.joystick.init()` : Initializes communication with the wheel, over USB.

#### For device detection and connection
* `pygame.joystick.get_count()` : Getter of number of available devices connected.
* `wheel = pygame.joystick.Joystick(index)` : Setup of the index-th wheel.
* `wheel.init()` : Initialization of wheel params.

#### For real-time event polling and axis reading 
* `pygame.event.pump()`: Setting up event polling from the wheel.
* `raw_axis = self.wheel.get_axis(0)` : Fetching the physical sterring position from the primary analog axis. 

#### For resource shutdown
* `pygame.quit()`: Ensures proper shutdown of the Pygame subsystem upon closing the application window. 

---
title: Moza Pit House Software Options
description: Comprehensive configuration profile and advanced parameter tuning guide for the Moza Pit House control software within the CAPT Motor dashboard ecosystem.
---

# Moza Pit House Software Options

<div class="grid cards" markdown>

-   **Base Configuration**

    ---

    Defines core operational limits including maximum steering rotation angles and overall force feedback intensity scalers.

-   **Haptic Equalization**

    ---

    Isolates and tunes frequency bands to balance high-frequency road textures against heavy low-frequency chassis loads.

-   **Mechanical Simulation**

    ---

    Applies algorithmic damping, friction, and inertia parameters to emulate real-world steering column weight and resistance.

</div>

---

## Configuration Parameter Matrix

The Moza Pit House software suite exposes a granular set of tuning parameters designed to align virtual simulation physics with physical direct-drive hardware responses.

| Parameter Category | Configuration Option | Operational Description |
| :--- | :--- | :--- |
| **Basic Limits** | **`Maximum Steering Angle`** | Sets the total physical rotation range (e.g., 540 degrees for formula profiles or 900 degrees for GT and road setups). |
| **Basic Limits** | **`Game Force Feedback Intensity`** | Global multiplier scaling the magnitude of forces transmitted from the simulation environment to the wheel base. |
| **Advanced Feel** | **`Road Sensitivity`** | Adjusts the amplification filter governing surface details, bumps, curbs, and high-frequency vibrations. |
| **Advanced Feel** | **`Natural Inertia`** | Simulates the rotational mass of a physical steering shaft to prevent overly light or twitchy center responses. |
| **Mechanicals** | **`Wheel Friction`** | Introduces a baseline mechanical drag to mimic steering box friction or power-steering resistance. |
| **Mechanicals** | **`Wheel Damping`** | Applies velocity-dependent resistance to stabilize high-speed oscillations and reduce violent wheel snap. |
| **Equalizer** | **`FFB Effect Equalizer`** | Frequency-based slider array used to boost or attenuate specific physical feedback characteristics. |

---

## Implementation Guidelines

> **Critical Warning:** Modifications to maximum torque output and inertia scaling must be tested in a controlled environment to ensure operator safety during high-speed transient maneuvers and sudden loss-of-control scenarios.

### Tuning Procedure

1. **Profile Selection:** Create a dedicated preset profile within Moza Pit House specifically calibrated for the CAPT Motor dashboard interface.
2. **Angle Synchronization:** Ensure the software rotation limit matches the active simulation target parameters to prevent mapping skew between virtual steering inputs and physical endpoints.
3. **Damping Calibration:** Incrementally adjust wheel damping and friction values to eliminate high-frequency resonance on the direct-drive motor base.

## SDK useful download information

1. Download the Moza SDK zip file from Moza's official website.

2. Extract the zip file.

3. Create a cs file using the index files in the docEng section of the extracted zip

4. Create a new folder with Visual studio or any other related software (cs console app) and copy in the `slnx` path the three dll files from the `MOZA_SDK/SDK_CSharp/x64` that relate to the moza libraries to be linked to your console project. 

5. Log into the project file and in the terminal execute the command: `dotnet build -c Release -r win-x64` to build the project.

6. Log into the project file and in the terminal execute the command: `dotnet run -c Release -r win-x64` to run the cs script.


## Basic commands overview (tried CSharp only, must work accordingly with C++ too) & Reference Guide

This section outlines useful C# SDK methods and commands commonly used for integrating with the MOZA Racing ecosystem for telemetry acquisition, device discovery, and force feedback control.

---

## 1. Initialization and Device Management

* **`MozaSDK.Initialize()`**
  * **Explanation:** Initializes the native MOZA SDK runtime environment. This must be called at the startup of your C# application before attempting to communicate with any hardware.

* **`MozaSDK.EnumerateDevices()`**
  * **Explanation:** Scans and detects connected MOZA hardware (wheelbases, steering wheels, pedals, and shifters) through the background service or Pit House runtime.

* **`MozaSDK.Release()`**
  * **Explanation:** Safely shuts down and unloads the SDK binding, freeing up internal handles and closing active data pipelines when your application closes.

---

## 2. Telemetry & Real-Time Data Acquisition (HID)

* **`WheelbaseData.GetSteeringAngle()`**
  * **Explanation:** Retrieves the real-time angular position of the steering wheel shaft, typically returned in degrees or radians.

* **`WheelbaseData.GetAngularVelocity()`**
  * **Explanation:** Fetches the current rotational speed of the wheel base. Useful for tracking fast counter-steering or damping inputs.

* **`WheelbaseData.GetAngularAcceleration()`**
  * **Explanation:** Pulls high-frequency acceleration metrics directly from the wheelbase's internal IMU/encoder calculations.

* **`WheelbaseData.GetTorqueOutput()`**
  * **Explanation:** Reads the active torque being delivered or experienced on the motor shaft (measured in Nm).

---

## 3. Force Feedback (FFB) Effect Control

* **`FFB.SetConstantForce(float magnitude)`**
  * **Explanation:** Sends a steady, constant torque command to the motor base (useful for centering springs or constant load simulations).

* **`FFB.SetSpringEffect(float coefficient, float saturation)`**
  * **Explanation:** Configures and applies a virtual spring effect, returning the wheel to center based on a proportional stiffness gradient.

* **`FFB.SetDamperEffect(float coefficient)`**
  * **Explanation:** Applies a dampening resistance force counter to the steering velocity to simulate fluid friction or power-steering weight.

* **`FFB.DisableAllEffects()`**
  * **Explanation:** Instantly cuts or clears all active force feedback loops sent by the application as a safety failsafe.

---

## 4. Device Parameters Configuration

* **`DeviceParams.SetMaxTorqueLimit(float torqueNm)`**
  * **Explanation:** Programmatically sets the peak torque ceiling for safety compliance (e.g., locking an R5 base to its maximum limit of 5.5 Nm).

* **`DeviceParams.SetMaximumRotationAngle(int degrees)`**
  * **Explanation:** Adjusts the hardware lock angle (e.g., setting rotation limits to 540° or 900°) directly from software.