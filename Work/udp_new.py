import socket
import struct
import time

# Set up local loopback UDP target
UDP_IP = "127.0.0.1" # Firewall ignores this address
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Navigate to your online variables natively
    platform = Application.PlatformManager.ActivePlatform
    model_root = platform.ActiveApplication.ModelRoot
    
    # CHANGE THIS to match your exact ControlDesk variable path
    my_var = model_root.GetVariableByPath("Model Root/MySubsystem/MySignalName")
    
    print("Streaming variables over local UDP port 5005...")
    
    # Broadcast Loop
    while True:
        live_value = float(my_var.Value)
        
        # Pack the float value into binary data ('d' means double precision float)
        packet = struct.pack("<d", live_value)
        
        # Shoot it locally on the machine
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        time.sleep(0.01) # 100 Hz broadcast rate

except Exception as e:
    print(f"UDP Broadcast Error: {e}")
