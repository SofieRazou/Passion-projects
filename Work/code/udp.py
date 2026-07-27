import socket
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import time
import sys

from shared_mem_manager import SManager

# --- Incoming Network Configuration ---
UDP_IP = "134.105.60.99"
UDP_PORT = 55001

# --- Outgoing Network Configuration (Simulink Forwarding) ---
FORWARD_IP = "134.105.60.99"  # Same IP
FORWARD_PORT = 55002          # Destination port for Simulink UDP Receive block

PACKET_SIZE = 16
PACKET_FORMAT = '<4f' # Expected incoming input from dSPACE/Simulink (4 floats = 16 bytes)

MEM_NAME = "shared_mem"

# 1. Receiver socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(6)

# 2. Forwarder socket (for sending angle to Simulink)
forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")
print(f"Forwarding live Angle to {FORWARD_IP}:{FORWARD_PORT}...")

manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)

angle = []
torque = []
phase1 = []
phase2 = []
values = [angle, torque, phase1, phase2]

start_time = time.time()
time_arr = []
time.sleep(0.1)  # Allow time for the sender to start sending data


def main(): 
    print("Shared memory created. Press Ctrl+C to exit.")

    start_time = time.time()
    i = 0
    try:
        while time.time() - start_time < 30:
            packet, addr = sock.recvfrom(2048)
            t = time.time() - start_time
            if len(packet) == PACKET_SIZE:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

                # --- FORWARD ANGLE TO SIMULINK ---
                # Packs single angle value as 8-byte double ('<d')
                angle_payload = struct.pack('<d', float(angle_val))
                forward_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

                # --- WRITE TO SHARED MEMORY ---
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val
                time_arr.append(t)
                
                print(f"LIVE Angle: {angle_val:.2f}° (Forwarded to {FORWARD_PORT}) | Torque: {torque_val:.2f} Nm")
                i += 1
            
    except (KeyboardInterrupt, socket.timeout):
        print("Exiting...")
    finally:
        print("Measured data registered in shared memory.")
        sock.close()
        forward_sock.close()

if __name__ == "__main__":
    main()






# import socket
# import struct
# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np 
# import time
# import sys

# from  shared_mem_manager import SManager


# # UDP_IP = "134.105.60.99"
# # UDP_PORT = 55001

# UDP_IP = "127.0.0.1"
# UDP_PORT = 5005
# PACKET_SIZE = 8
# PACKET_FORMAT = '<d' # the one outputed by the simulink blocks


# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind((UDP_IP, UDP_PORT))
# sock.settimeout(6)

# print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

# manager = SManager()
# sm, mem_data = manager.create_mem(mem_name="shared_mem", size=PACKET_SIZE)


# def plot_signal(data, time_arr):
#     plt.figure(figsize=(8,8))
#     plt.plot(time_arr, data, marker='o', linestyle='-', color='b')
#     plt.title("Received Signal")
#     plt.xlabel("Time (s)")
#     plt.ylabel("Signal Value(deg)")
#     plt.grid()
#     plt.show()

# def main():
#     if values:
#         plot_signal(values, time_arr=time_arr)
#     else:
#         print("No data received.")

# start_time = time.time()
# values = []
# time_arr = []
# time.sleep(0.1)  # Allow time for the sender to start sending data


# def main():
    
#     print("Shared memory created. Press Ctrl+C to exit.")

#     start_time = time.time()
#     try:
#         while True:
#             packet, addr = sock.recvfrom(1024)
#             t = time.time() - start_time
#             if len(packet) == PACKET_SIZE: #i think 64 for the torque, angle and phase current outputs 
#                     value= struct.unpack(PACKET_FORMAT, packet)[0]
#                     values.append(value)
#                     mem_data[0] = value
#                     time_arr.append(t)
#                     print(f"Succesfully received angle: {value:.2f} degrees")
            
#     except KeyboardInterrupt or socket.timeout:
#         print("Exiting...")
#     finally:
#         print("Data registred in shared memory")
#         sock.close()
#     if values :
#         plot_signal(values, time_arr=time_arr)
#     else:
#         print("No data received.")
#     # finally:
#     #     manager.close()
#     #     manager.deallocate()
#     #     print("Shared memory deallocated.") 

# if __name__ == "__main__":
#     main()
import socket
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import time
import sys

from  shared_mem_manager import SManager


UDP_IP = "134.105.60.99"
UDP_PORT = 55001

# UDP_IP = "127.0.0.1"
# UDP_PORT = 5005
PACKET_SIZE = 16
PACKET_FORMAT = '<4f' # the one outputed by the simulink blocks

MEM_NAME = "shared_mem"


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(6)

print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)

angle = []
torque = []
phase1 = []
phase2 = []
values = [angle, torque, phase1, phase2]

# def plot_signal(data, time_arr, title, yname):
#     plt.figure(figsize=(6,6))
#     plt.plot(time_arr, data, marker='o', linestyle='-', color='b')
#     plt.title(title)
#     plt.xlabel("Time (s)")
#     plt.ylabel(yname)
#     plt.grid()
#     plt.show()


start_time = time.time()


time_arr = []
time.sleep(0.1)  # Allow time for the sender to start sending data


def main(): 
    print("Shared memory created. Press Ctrl+C to exit.")

    start_time = time.time()
    i = 0
    try:
        while time.time() - start_time < 30:
            packet, addr = sock.recvfrom(16)
            t = time.time() - start_time
            if len(packet) == PACKET_SIZE: #i think 64 for the torque, angle and phase current outputs 
                    angle, torque, phase1, phase2= struct.unpack(PACKET_FORMAT, packet)

                    #writing stats in shared memory 
                    mem_data[0] = angle
                    mem_data[1] = torque
                    mem_data[2] = phase1
                    mem_data[3] = phase2
                    time_arr.append(t)
                    
                    print(f"LIVE Angle: {angle:.2f} degrees")
                    print(f"LIVE Torque: {torque:.2f} Nm")
                    print(f"LIVE Current of Phase 1: {phase1:.2f} Amps")
                    print(f"LIVE Current of Phase 2 : {phase2:.2f} Amps")
                    #iterate through the 4 different data stats 
                    i = i+1
            
    except KeyboardInterrupt or socket.timeout:
        print("Exiting...")
    finally:
        print("Measured data registred in shared memory")
        sock.close()
    # if values :
    #     plot_signal(values, time_arr=time_arr)
    # else:
    #     print("No data received.")
    # finally:
    #     manager.close()
    #     manager.deallocate()
    #     print("Shared memory deallocated.") 

if __name__ == "__main__":
    main()
