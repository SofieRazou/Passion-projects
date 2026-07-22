
Execution Error: (-2147352567, 'Exception occurred.', (0, 'dSPACE.PlatformManagement.Foundation', 'Value does not fall within the expected range.', None, 0, -2147024809), None)



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

    if experiment.Platforms.Count == 0:
        print("ERROR: No hardware platform bound to this experiment.")
        sys.exit()
        
    platform = experiment.Platforms.Item(1) 
    print(f"Found Active Hardware Platform: {platform.Name}")

    var_desc = platform.ActiveVariableDescription
    dataset = var_desc.DataSets.WorkingDataSet
    print("Successfully hooked into the live dSPACE memory map.")

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


