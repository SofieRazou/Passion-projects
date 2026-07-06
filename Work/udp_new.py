import socket
import struct
import time

# 1. Setup local loopback UDP target (Ignored by Windows Firewall)
UDP_IP = "127.0.0.1" 
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # 2. Use ControlDesk's direct object bypass
    # 'ActiveExperiment' is a built-in global variable inside the interpreter console!
    var_manager = ActiveExperiment.VariableManager
    
    # !!! CHANGE THIS to your exact copied path !!!
    signal_path = "Model Root/MySubsystem/MySignalName" 
    my_var = var_manager.GetVariableByPath(signal_path)
    
    print("SUCCESS: Streaming variables over local UDP port 5005...")
    print("Click 'Stop' in the script toolbar to halt.")
    
    # 3. Local UDP broadcast loop
    while True:
        # Fetch the current value from the variable object
        live_value = float(my_var.Value)
        
        # Pack into binary data ('d' represents 8-byte double precision float)
        packet = struct.pack("<d", live_value)
        
        # Send it locally inside the PC network card
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # 100 Hz refresh loop
        time.sleep(0.01) 

except Exception as e:
    print(f"UDP Broadcast Error: {e}")
