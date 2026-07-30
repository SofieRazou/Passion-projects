import socket
import struct
import math
import time

# Target configuration (Localhost for Simulink)
IP = "127.0.0.1"
PORT_BLOCK_1 = 5005  # Simulink UDP Receive 1 Local Port
PORT_BLOCK_2 = 5006  # Simulink UDP Receive 2 Local Port

# Create non-blocking UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

print("=" * 60)
print(f"UDP Stream Started: Transmitting to {IP}")
print(f" -> Channel 1 Target Port: {PORT_BLOCK_1} (Data Type: double x2)")
print(f" -> Channel 2 Target Port: {PORT_BLOCK_2} (Data Type: int32 x2)")
print("=" * 60 + "\n")

t = 0.0
dt = 0.05  # 20 Hz transmission rate matching Simulink sample time
packet_count = 0

try:
    while True:
        packet_count += 1

        # --- Channel 1 Payload: Sine + Cosine (2 x double) ---
        val1_a = math.sin(t)
        val1_b = math.cos(t)
        payload_1 = struct.pack('>2d', val1_a, val1_b)  # Big-Endian 64-bit floats

        # --- Channel 2 Payload: Counter + Binary Flag (2 x int32) ---
        val2_a = packet_count
        val2_b = 1 if (packet_count % 20 < 10) else 0
        payload_2 = struct.pack('>2i', val2_a, val2_b)  # Big-Endian 32-bit ints

        # --- Transmit Data ---
        bytes_sent_1 = sock.sendto(payload_1, (IP, PORT_BLOCK_1))
        bytes_sent_2 = sock.sendto(payload_2, (IP, PORT_BLOCK_2))

        # --- Console Verification Printouts ---
        print(f"[Packet #{packet_count:04d}]")
        print(f"  └─ Port {PORT_BLOCK_1} | Sent {bytes_sent_1} bytes | Values: [sin={val1_a:+.4f}, cos={val1_b:+.4f}]")
        print(f"  └─ Port {PORT_BLOCK_2} | Sent {bytes_sent_2} bytes | Values: [count={val2_a}, flag={val2_b}]")
        print("-" * 60)

        t += dt
        time.sleep(dt)

except KeyboardInterrupt:
    print("\nTransmission stopped by user.")
finally:
    sock.close()
    print("Socket closed cleanly.")
