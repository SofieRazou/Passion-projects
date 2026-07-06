import socket
import struct
import time
import sys

# 1. Network Configuration (Preserving your settings)
UDP_IP = "134.105.60.99"
UDP_PORT = 55001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

try:
    active_platforms = Application.ActiveExperiment.Platforms
    if len(active_platforms) == 0:
        raise RuntimeError("No active platform found.")
        
    my_platform = active_platforms[0]
    variables_collection = my_platform.ActiveVariableDescription.Variables
    
    # 2. DYNAMIC PATH DISCOVERY LOOP
    print("Searching the backend API for your hardware channel...")
    discovered_path = None
    
    # Scan all backend keys for 'ch16' to find the real string Python wants
    for key in variables_collection.Keys:
        if "ch16" in key.lower() and "out1" in key.lower():
            discovered_path = key
            break
            
    # If the exact combined match fails, look for just 'ch16'
    if not discovered_path:
        for key in variables_collection.Keys:
            if "ch16" in key.lower():
                discovered_path = key
                break

    if discovered_path is None:
        print("\n[CRITICAL ERROR]: Could not find any variable in the backend map containing 'Ch16'.")
        print("Please verify the variable is fully loaded in your Variable Browser.")
    else:
        print(f"\n[SUCCESS]: Found real API path: '{discovered_path}'")
        my_var = variables_collection[discovered_path]
        print(f"Streaming live data to {UDP_IP}:{UDP_PORT}... Click 'Stop' to halt.")
        
        # 3. Main UDP Loop
        while True:
            raw_val = my_var.Value
            
            if raw_val is None or "unknown" in str(raw_val).lower():
                time.sleep(0.01)
                continue
                
            live_value = float(raw_val)
            packet = struct.pack("<d", live_value)
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            time.sleep(0.01) 

except Exception as e:
    import traceback
    print("\n--- LOOP FAILURE DETAILS ---")
    print(traceback.format_exc())

