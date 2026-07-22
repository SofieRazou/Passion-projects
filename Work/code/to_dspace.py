import win32com.client
import time
import sys

try:
    # 1. Connect to the next-gen application layer
    cd = win32com.client.Dispatch("ControlDeskNG.Application")
    print("Successfully connected to ControlDesk 7.5!")
    
    # 2. Safely grab the active experiment
    experiment = cd.ActiveExperiment
    if experiment is None:
        print("ERROR: No active experiment found. Please open an experiment in ControlDesk first.")
        sys.exit()
        
    # 3. Get the variables list
    variables = experiment.Variables
    print("Successfully mapped ControlDesk variables!")

    # 4. Target your specific Simulink signal path
    # CHANGE THIS STRING to match your exact variable name in the ControlDesk tree!
    my_signal = variables.Item("Model Root/Subsystem/MySignal")

    # Real-time polling loop
    print("Starting live data stream... Press Ctrl+C to stop.")
    while True:
        live_value = my_signal.Value
        print(f"Live Data: {live_value}")
        time.sleep(0.01) # Polls at ~100Hz

except AttributeError as ae:
    print(f"\nStructure Error: {ae}")
    print("Verify that your project is fully loaded and you are 'Online' in ControlDesk.")
except Exception as e:
    print(f"\nAn error occurred: {e}")

