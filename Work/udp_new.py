import socket
import struct
import time

# 1. Setup local loopback UDP target (Ignored by Windows Firewall)
UDP_IP = "127.0.0.1" 
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # 2. Correct 7.5 Variable Architecture Mapping
    # Get the active hardware platform from your online experiment
    my_platform = Application.ActiveExperiment.Platforms["Platform"]
    
    # Target your specific variable out of the active hardware description map
    # !!! YOU MUST paste your exact copied path string inside the brackets below !!!
    my_var = my_platform.ActiveVariableDescription.Variables["Platform()://Model Root/MySubsystem/MySignalName"]
    
    print("SUCCESS: Streaming variables over local UDP port 5005...")
    print("Click 'Stop' in the script toolbar to halt.")
    
    # 3. Local UDP broadcast loop
    while True:
        # Fetch the live value from the platform memory cache
        live_value = float(my_var.Value)
        
        # Pack into binary data ('d' represents an 8-byte double precision float)
        packet = struct.pack("<d", live_value)
        
        # Send it locally inside your PC network card
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # 100 Hz refresh loop
        time.sleep(0.01) 

except Exception as e:
    print(f"UDP Broadcast Error: {e}")

