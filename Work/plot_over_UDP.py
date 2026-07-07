import socket
import struct
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

UDP_IP = "0.0.0.0"      # listen on all interfaces
UDP_PORT = 5005

# Example packet: 4 floats = torque, angle, currentA, currentB
PACKET_FORMAT = "<ffff"   # little-endian, 4 float32
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

N = 500
t_data = deque(maxlen=N)
torque_data = deque(maxlen=N)
angle_data = deque(maxlen=N)
ia_data = deque(maxlen=N)
ib_data = deque(maxlen=N)

start_time = time.time()

fig, ax = plt.subplots()
line_torque, = ax.plot([], [], label="Torque")
line_angle, = ax.plot([], [], label="Angle")
line_ia, = ax.plot([], [], label="Current A")
line_ib, = ax.plot([], [], label="Current B")

ax.set_xlabel("Time [s]")
ax.set_ylabel("Value")
ax.grid(True)
ax.legend()

def update(frame):
    while True:
        try:
            packet, addr = sock.recvfrom(1024)

            if len(packet) >= PACKET_SIZE:
                torque, angle, ia, ib = struct.unpack(PACKET_FORMAT, packet[:PACKET_SIZE])

                now = time.time() - start_time

                t_data.append(now)
                torque_data.append(torque)
                angle_data.append(angle)
                ia_data.append(ia)
                ib_data.append(ib)

        except BlockingIOError:
            break

    if len(t_data) > 0:
        line_torque.set_data(t_data, torque_data)
        line_angle.set_data(t_data, angle_data)
        line_ia.set_data(t_data, ia_data)
        line_ib.set_data(t_data, ib_data)

        ax.set_xlim(max(0, t_data[-1] - 10), t_data[-1] + 0.1)

        all_values = list(torque_data) + list(angle_data) + list(ia_data) + list(ib_data)
        ax.set_ylim(min(all_values) - 1, max(all_values) + 1)

    return line_torque, line_angle, line_ia, line_ib

ani = FuncAnimation(fig, update, interval=20)
plt.show()
