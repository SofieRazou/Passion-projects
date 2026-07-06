import socket
import struct
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 
import time
import sys

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

PACKET_FORMAT = '<d' # the one outputed by the simulink blocks


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(0.1)

print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

def plot_signal(data):
    plt.figure(figsize=(8,8))
    plt.plot(time_arr, data, marker='o', linestyle='-', color='b')
    plt.title("Received Signal")
    plt.xlabel("Time (s)")
    plt.ylabel("Signal Value(deg)")
    plt.grid()
    plt.show()

def main():
    if values:
        plot_signal(values)
    else:
        print("No data received.")

start_time = time.time()
values = []
time_arr = []
while True:
    try:
       
                data, addr = sock.recvfrom(1024)
                t = time.time() - start_time
                if len(data) == 8:
                    value= struct.unpack(PACKET_FORMAT, data)[0]
                    values.append(value)
                    time_arr.append(t)
                    print(f"Succesfully received angle: {value:.2f} degrees")
    except socket.timeout:
             main()     
            

    except KeyboardInterrupt:
        print("Receiver-end interrupted.")
        sock.close()


