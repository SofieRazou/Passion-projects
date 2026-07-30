import socket
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import time
import sys

from  shared_mem_manager import SManager


# UDP_IP = "134.105.60.99"
# UDP_PORT = 55001

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
FORWARD_PORT = 5006
PACKET_SIZE = 32
PACKET_FORMAT = '<4d' # the one outputed by the simulink blocks

MEM_NAME = "shared_mem"


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)
# sock.bind((UDP_IP, UDP_PORT))
# sock.settimeout(6)

t = 0.0
dt = 0.05  # 20 Hz transmission rate matching Simulink sample time

# forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")
print(f"Forwarding live Angle to {UDP_IP}:{FORWARD_PORT}...")

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
            packet, addr = sock.recvfrom(PACKET_SIZE)
            t = time.time() - start_time
            if len(packet) == PACKET_SIZE: #i think 64 for the torque, angle and phase current outputs 
                    # angle, torque, phase1, phase2, imped, admit= struct.unpack(PACKET_FORMAT, packet)
                    angle, torque, phase1, phase2 = struct.unpack(PACKET_FORMAT, packet)

                    #writing stats in shared memory 
                    mem_data[0] = angle
                    mem_data[1] = torque
                    mem_data[2] = phase1
                    mem_data[3] = phase2
                    # mem_data[4] = imped
                    # mem_data[5] = admit 
                    time_arr.append(t)
                     # Angle = 0.1*t + 2
                    sof = 0.1 * t + 2.0
                    
                            # Pack as a double (8 bytes)
                    data = struct.pack('>2d', sof)
                    
                            # Send
                    sock.sendto(data, (UDP_IP,FORWARD_PORT))
                    
                    print(f"t = {t:.3f} s, sof = {sof:.3f}")
                    
                            # 100 Hz update rate
                    time.sleep(0.01)

                    
                    print(f"LIVE Angle: {angle:.2f} degrees")
                    print(f"LIVE Torque: {torque:.2f} Nm")
                    print(f"LIVE Current of Phase 1: {phase1:.2f} Amps")
                    print(f"LIVE Current of Phase 2 : {phase2:.2f} Amps")
                    # print(f"LIVE Impedance: {imped:.2f}")
                    # print(f"LIVE Admittance: {admit:.2f}")
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
