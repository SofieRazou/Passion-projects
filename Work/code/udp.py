import socket
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import time
import sys

from  SManager import create_mem


# UDP_IP = "134.105.60.99"
# UDP_PORT = 55001

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
PACKET_SIZE = 4
PACKET_FORMAT = '<f' # the one outputed by the simulink blocks


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(6)

print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

sm, mem_data = create_mem(mem_name="udp_share", size=4)


def plot_signal(data, time_arr):
    plt.figure(figsize=(8,8))
    plt.plot(time_arr, data, marker='o', linestyle='-', color='b')
    plt.title("Received Signal")
    plt.xlabel("Time (s)")
    plt.ylabel("Signal Value(deg)")
    plt.grid()
    plt.show()

def main():
    if values:
        plot_signal(values, time_arr=time_arr)
    else:
        print("No data received.")

start_time = time.time()
values = []
time_arr = []
time.sleep(0.1)  # Allow time for the sender to start sending data
while True:
    try:
       
                mem_data, addr = sock.recvfrom(1024)
                t = time.time() - start_time
                if len(mem_data) == PACKET_SIZE: #i think 64 for the torque, angle and phase current outputs 
                    value= struct.unpack(PACKET_FORMAT, mem_data)[0]
                    values.append(value)
                    time_arr.append(t)
                    print(f"Succesfully received angle: {value:.2f} degrees")
    except socket.timeout:
             print("No data received within the timeout period.")
             break    
            

    except KeyboardInterrupt:
        print("Receiver-end interrupted.")
        sock.close()

if values :
     plot_signal(values, time_arr=time_arr)
else:
    print("No data received.")
