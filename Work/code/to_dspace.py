import win32com.client
import time

# Connect to the open ControlDesk instance
cd = win32com.client.Dispatch("ControlDesk.Application")
experiment = cd.ActiveExperiment
variables = experiment.Variables

# Target your specific Simulink signal path
my_signal = variables.Item("Model Root/Subsystem2/Torque")

# Real-time loop for your GUI
while True:
    live_value = my_signal.Value
    print(f"Live Data: {live_value}")

    # Update your Python GUI widgets here (Tkinter, PyQt, etc.)
    time.sleep(0.01) # Polls at ~100Hz
