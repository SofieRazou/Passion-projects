import socket
import struct
import time

# 1. Network Configuration
UDP_IP = "134.105.60.99"
UDP_PORT = 55001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# The UI path string that you copied exactly
VAR_PATH = r'Platform()://Model Root/Subsystem2/Ch16/Out1'

try:
    active_platforms = Application.ActiveExperiment.Platforms
    if len(active_platforms) == 0:
        raise RuntimeError("No active platform found.")
        
    my_platform = active_platforms[0]
    
    print(f"Connected to Platform: {my_platform.Name}")
    print("Forcing direct memory poll to stream variable...")
    print("Click 'Stop' in the script toolbar to halt.")
    
    # 2. Main UDP Direct Loop
    while True:
        # Bypass the dictionary lookup by reading directly from the platform interface
        try:
            raw_val = my_platform.ReadVariable(VAR_PATH)
        except Exception:
            # If the platform itself is busy or locking, wait and try again
            time.sleep(0.01)
            continue
            
        # Guard against uninitialized/Unknown hardware data states
        if raw_val is None or "unknown" in str(raw_val).lower():
            time.sleep(0.01)
            continue
            
        live_value = float(raw_val)
        
        # Pack into binary data (8-byte double precision float)
        packet = struct.pack("<d", live_value)
        
        # Stream out over network socket
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # 100 Hz loop refresh
        time.sleep(0.01)

except Exception as e:
    import traceback
    print("\n--- LOOP FAILURE DETAILS ---")
    print(traceback.format_exc())

