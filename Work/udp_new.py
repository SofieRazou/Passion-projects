my_platform = Application.ActiveExperiment.Platforms["Platform"]
variables_collection = my_platform.ActiveVariableDescription.Variables

print("--- Real Python API Keys ---")
for key in variables_collection.Keys:
    if "ch16" in key.lower():
        print(f"PASTE THIS EXACT STRING: r'{key}'")


import socket
import struct
import time

# 1. Setup local loopback UDP target (Keeping your exact configuration)
UDP_IP = "134.105.60.99"
UDP_PORT = 55001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# 2. Hardcoded path exactly as it's targeted in the backend map
# Note: The 'r' ensures the backslash in Ch16\Out1 is treated as text, not an escape character
VAR_PATH = r'Platform()://Model Root/Subsystem2/Ch16/Out1'

try:
    my_platform = Application.ActiveExperiment.Platforms["Platform"]
    variables_collection = my_platform.ActiveVariableDescription.Variables
    
    # Check if the hardware map contains this path before querying it
    if VAR_PATH not in variables_collection:
        print(f"ERROR: '{VAR_PATH}' not found in the active layout collection.")
        print("Verify if your I/O folder is named 'Analog Outputs' or similar in the layout.")
    else:
        my_var = variables_collection[VAR_PATH]
        print(f"SUCCESS: Streaming hardware variable {VAR_PATH} over UDP port 55001...")
        print("Click 'Stop' in the script toolbar to halt.")
        
        # 3. Local UDP loop
        while True:
            raw_val = my_var.Value
            
            # Guard against dSPACE "Unknown" or None state when hardware is initializing
            if raw_val is None or str(raw_val) == "Unknown":
                time.sleep(0.01)
                continue
                
            live_value = float(raw_val)
            
            # Pack into binary data ('d' represents an 8-byte double precision float)
            packet = struct.pack("<d", live_value)
            
            # Send it locally inside your PC network card
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            
            # 100 Hz refresh loop
            time.sleep(0.01) 

except Exception as e:
    print(f"UDP Broadcast Error: {e}")

