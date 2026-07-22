for i in range(1, 6): print(Application.ActiveExperiment.Platforms.Item(1).ActiveVariableDescription.DataSets.WorkingDataSet.Parameter.Item(i).Path)

plat = Application.ActiveExperiment.Platforms.Item(1)
map = plat.ActiveVariableDescription.DataSets.WorkingDataSet
myVar = map.Parameter.Item("Model Root/Subsystem2/Torque")
print(myVar.Value)


import win32com.client
import time
import sys

try:
    cd = win32com.client.Dispatch("ControlDeskNG.Application")
    print("Connected to ControlDesk 7.5!")

    experiment = cd.ActiveExperiment
    if experiment is None:
        print("ERROR: No active experiment open in ControlDesk.")
        sys.exit()

    # SAFE CHECK: Loop through platforms instead of calling Item(1)
    platform = None
    for p in experiment.Platforms:
        platform = p
        break

    if platform is None:
        print("ERROR: No active hardware platform found in this experiment.")
        sys.exit()
        
    print(f"Found Active Hardware Platform: {platform.Name}")

    # SAFE CHECK: Verify the variable description is actually ready
    var_desc = platform.ActiveVariableDescription
    if var_desc is None:
        print("ERROR: Variable description file (.trc) is not loaded. Is ControlDesk Online?")
        sys.exit()

    dataset = var_desc.DataSets.WorkingDataSet
    
    # Change this to a real variable name from your Simulink model
    test_path = "Model Root/Subsystem/MySignal" 

    try:
        my_signal = dataset.Parameter.Item(test_path)
        print("Success! Target variable found.")
    except Exception:
        print(f"\nPath '{test_path}' not found in the live map.")
        print("--------------------------------------------------")
        print("PRINTING RECENT VARIABLES IN YOUR MODEL ENGINE:")
        count = min(10, dataset.Parameter.Count)
        for i in range(1, count + 1):
            print(f"   Valid Path option: {dataset.Parameter.Item(i).Path}")
        print("--------------------------------------------------")
        sys.exit()

    print("\nStreaming real-time data... Press Ctrl+C to stop.\n")
    while True:
        live_value = my_signal.Value
        print(f"Live Variable Value: {live_value}")
        time.sleep(0.01)

except Exception as e:
    print(f"\nExecution Error: {e}")


