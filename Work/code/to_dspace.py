import win32com.client
import time


cd = win32com.client.Dispatch("ControlDesk.Application")
experiment = cd.ActiveExperiment
variables = experiment.Variables

torque_signal = variables.Item("Model Root/Subsystem2/Torque")

while True:
    live_value = torque_signal.Value
    print(f"Live Data: {live_value}")
    time.sleep(0.01) # Polls at ~100Hz
