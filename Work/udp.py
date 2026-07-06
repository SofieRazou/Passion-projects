import socket
import struct

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

PACKET_FORMAT ="dddd" # the one outputed by the simulink blocks


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

filename = "capt_logs.csv"
# pass and add prints outs 

while True:
    angle = float(input("Angle:"))
    torque = float(input("Torque:"))
    amp1 = float(input("Phase current 1"))
    amp2 = float(input("Phase current 2"))

    packet = struct.pack(
        "dddd",
        angle,
        torque,
        amp1,
        amp2
    )

    sock.sendto(packet, (UDP_IP, UDP_PORT))
