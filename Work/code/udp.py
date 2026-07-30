import socket
import struct
import time
from shared_mem_manager import SManager

# --- Network Configuration ---
UDP_IP = "127.0.0.1"      # Localhost IP
UDP_PORT_LISTEN = 5005   # Fetch incoming dSPACE/Simulink info here
FORWARD_IP = "127.0.0.1"  # Localhost IP
FORWARD_PORT = 5006      # Destination port for Simulink Angle UDP Receive block

# Packet Configuration: 4 single-precision floats (4 x 4 bytes = 16 bytes)
PACKET_SIZE = 16
PACKET_FORMAT = '<4f'     # Little-Endian, 4 floats

MEM_NAME = "shared_mem"

# --- 1. Set Up Receiver Socket ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((UDP_IP, UDP_PORT_LISTEN))
recv_sock.setblocking(False)  # Non-blocking mode

# --- 2. Set Up Forwarder Socket ---
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 60)
print(f"Fetching UDP info on   -> {UDP_IP}:{UDP_PORT_LISTEN} (Non-blocking)")
print(f"Sending Angle info to  -> {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 60 + "\n")

# --- 3. Initialize Shared Memory ---
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)


def main():
    print("Shared memory allocated. Streaming started (Press Ctrl+C to stop)...\n")

    start_time = time.time()
    packet_count = 0

    try:
        # Run loop for 30 seconds
        while time.time() - start_time < 30:
            try:
                packet, addr = recv_sock.recvfrom(1024)
                
                if len(packet) == PACKET_SIZE:
                    # Unpack incoming 4 floats
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

                    # --- Write to Shared Memory ---
                    mem_data[0] = angle_val
                    mem_data[1] = torque_val
                    mem_data[2] = phase1_val
                    mem_data[3] = phase2_val

                    # --- Forward ONLY Angle Value to Simulink (as double '<d') ---
                    angle_payload = struct.pack('<d', float(angle_val))
                    fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

                    packet_count += 1
                    
                    # Console confirmation
                    print(f"[{packet_count:04d}] Fetched data from port {UDP_PORT_LISTEN} | "
                          f"Angle: {angle_val:6.2f}° | Torque: {torque_val:6.2f} Nm "
                          f"--> [Angle forwarded to port {FORWARD_PORT}]")

            except BlockingIOError:
                # Expected in non-blocking mode when no data is in the socket buffer
                pass

            time.sleep(0.005)  # Prevents high CPU usage

    except KeyboardInterrupt:
        print("\nManual stop triggered by user.")

    finally:
        print("\nCleaning up resources...")
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed cleanly.")


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
