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
PACKET_SIZE = 8
PACKET_FORMAT = '<d' # the one outputed by the simulink blocks


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(6)

print(f"I am ALIVEEEE! Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

manager = SManager()
sm, mem_data = manager.create_mem(mem_name="shared_mem", size=PACKET_SIZE)


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


def main():
    
    print("Shared memory created. Press Ctrl+C to exit.")

    start_time = time.time()
    try:
        while True:
            packet, addr = sock.recvfrom(1024)
            t = time.time() - start_time
            if len(packet) == PACKET_SIZE: #i think 64 for the torque, angle and phase current outputs 
                    value= struct.unpack(PACKET_FORMAT, packet)[0]
                    values.append(value)
                    mem_data[0] = value
                    time_arr.append(t)
                    print(f"Succesfully received angle: {value:.2f} degrees")
            
    except KeyboardInterrupt or socket.timeout:
        print("Exiting...")
    finally:
        print("Data registred in shared memory")
        sock.close()
    if values :
        plot_signal(values, time_arr=time_arr)
    else:
        print("No data received.")
    # finally:
    #     manager.close()
    #     manager.deallocate()
    #     print("Shared memory deallocated.") 

if __name__ == "__main__":
    main()
