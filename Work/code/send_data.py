import socket
import struct
import time
import math

# --- Network Settings ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# --- Vehicle Parameters ---
u = 30.0       # Speed [m/s]
L = 1.0        # Wheelbase [m]
dt = 0.01      # Time step [s] (100 Hz)

Y_max = 1.8    # Wobble lateral offset [m]
omega = 2.5    # Wobble frequency [rad/s]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"Streaming live UDP data to {UDP_IP}:{UDP_PORT}...")

start_time = time.perf_counter()
next_step = start_time
x = 0.0

try:
    while True:
        elapsed = time.perf_counter() - start_time

        # Calculate wobble steering (delta) and heading (theta)
        heading_tan = (Y_max * omega / u) * math.cos(omega * elapsed)
        theta = math.atan(heading_tan)

        steering_tan = (-L * Y_max * (omega ** 2) / (u ** 2)) * math.sin(omega * elapsed)
        delta = math.atan(steering_tan)

        # Advance forward position X
        x += u * math.cos(theta) * dt

        # Wrap theta to [-pi, pi] to prevent yaw overflow
        theta_wrapped = math.atan2(math.sin(theta), math.cos(theta))

        # IMPORTANT: '<ddd' specifies Little-Endian format for 3 doubles (24 bytes)
        payload = struct.pack('<ddd', float(x), float(delta), float(theta_wrapped))
        sock.sendto(payload, (UDP_IP, UDP_PORT))

        print(f"Sent -> X: {x:.2f} m | Delta: {math.degrees(delta):.2f}° | Theta: {math.degrees(theta_wrapped):.2f}°")

        # Keep 100 Hz timing
        next_step += dt
        sleep_time = next_step - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\nSender stopped.")
finally:
    sock.close()
