import numpy as np
import socket

UDP_IP = "192.168.0.10"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

trajectory = np.array([
    [1.0, 2.0],
    [3.0, 4.0],
    [5.0, 6.0]
], dtype=np.float32)

packet = trajectory.tobytes()

sock.sendto(packet, (UDP_IP, UDP_PORT))
