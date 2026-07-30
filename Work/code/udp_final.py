import socket
import struct
import math
import time

# Target configuration (Localhost)
IP = "127.0.0.1"
PORT_BLOCK_1 = 55001  # Simulink UDP Receive 1 Local Port
PORT_BLOCK_2 = 55002  # Simulink UDP Receive 2 Local Port

# Create non-blocking UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

print(f"Sending stream to Simulink ports {PORT_BLOCK_1} and {PORT_BLOCK_2}...")

t = 0.0
dt = 0.05  # Time step matching Simulink's Sample Time

try:
    while True:
        # --- Channel 1 Payload: Sine wave + Cosine wave (2 x double) ---
        val1_a = math.sin(t)
        val1_b = math.cos(t)
        # Pack two 64-bit floats ('d') into binary bytes
        payload_1 = struct.pack('>2d', val1_a, val1_b)  # '>2d' = Big-Endian, 2 doubles

        # --- Channel 2 Payload: Counter + Status Flag (2 x int32) ---
        val2_a = int(t * 10) % 100
        val2_b = 1 if (val2_a > 50) else 0
        # Pack two 32-bit integers ('i') into binary bytes
        payload_2 = struct.pack('>2i', val2_a, val2_b)  # '>2i' = Big-Endian, 2 ints

        # --- Send Simultaneously ---
        sock.sendto(payload_1, (IP, PORT_BLOCK_1))
        sock.sendto(payload_2, (IP, PORT_BLOCK_2))

        t += dt
        time.sleep(dt)  # Control transmission rate

except KeyboardInterrupt:
    print("\nStream stopped.")
finally:
    sock.close()
