# import socket
# import struct
# import time
# import math
# from shared_mem_manager import SManager

# # --- Network Configuration ---
# UDP_IP = "127.0.0.1"      # Localhost IP
# UDP_PORT_LISTEN = 5005   # Fetch incoming dSPACE/Simulink info here
# FORWARD_IP = "127.0.0.1"  # Localhost IP
# FORWARD_PORT = 5006      # Destination port for Simulink Angle UDP Receive block

# # Packet Configuration: 4 single-precision floats (4 x 4 bytes = 16 bytes)
# PACKET_SIZE = 16
# PACKET_FORMAT = '<4f'     # Little-Endian, 4 floats

# MEM_NAME = "shared_mem"

# # --- 1. Set Up Receiver Socket ---
# recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# recv_sock.bind((UDP_IP, UDP_PORT_LISTEN))
# recv_sock.setblocking(False)  # Non-blocking mode

# # --- 2. Set Up Forwarder Socket ---
# fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# print("=" * 60)
# print(f"Fetching UDP info on   -> {UDP_IP}:{UDP_PORT_LISTEN} (Non-blocking)")
# print(f"Sending Angle info to  -> {FORWARD_IP}:{FORWARD_PORT}")
# print("=" * 60 + "\n")

# # --- 3. Initialize Shared Memory ---
# manager = SManager()
# sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)

# ANGLE = 0.0
# def main():
#     print("Shared memory allocated. Streaming started (Press Ctrl+C to stop)...\n")

#     start_time = time.time()
#     packet_count = 0
#     t = 0.0

#     try:
#         # Run loop for 30 seconds
#         while time.time() - start_time < 30:
#             angle_to_send = 0.0
#             data_received = False

#             # --- Step A: Attempt to fetch real packet from port 5005 ---
#             try:
#                 packet, addr = recv_sock.recvfrom(1024)
                
#                 if len(packet) == PACKET_SIZE:
#                     # Unpack incoming 4 floats
#                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

#                     # Write to Shared Memory
#                     mem_data[0] = angle_val
#                     mem_data[1] = torque_val
#                     mem_data[2] = phase1_val
#                     mem_data[3] = phase2_val
#                     ANGLE = angle_val
#                     angle_to_send = float(angle_val)
#                     data_received = True

#             except BlockingIOError:
#                 # Expected when no data is buffered on port 5005
#                 data_received = False

#             # --- Step B: Fallback test signal if port 5005 is idle ---
#             if not data_received:
#                 angle_to_send = 45.0 * math.sin(t)  # Generates test sine wave [-45°, +45°]

#             # --- Step C: Forward angle to Simulink on port 5006 ---
#             angle_payload = struct.pack('<d', angle_to_send)
#             fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

#             packet_count += 1
#             mode_tag = "REAL DATA (5005)" if data_received else "FALLBACK SINE"

#             print(f"[{packet_count:04d}] [{mode_tag}] Sent Angle: {angle_to_send:6.2f}° --> Port {FORWARD_PORT}")

#             t += 0.05
#             time.sleep(0.05)  # 20 Hz loop rate for smooth Simulink reception

#     except KeyboardInterrupt:
#         print("\nManual stop triggered by user.")

#     finally:
#         print("\nCleaning up resources...")
#         recv_sock.close()
#         fwd_sock.close()
#         print("Sockets closed cleanly.")


# if __name__ == "__main__":
#     main()

# if __name__ == "__main__":
#     main()
import socket
import struct
import time
from shared_mem_manager import SManager

# --- Network Configuration ---
UDP_IP = "127.0.0.1"      # Localhost IP
UDP_PORT_LISTEN = 5005   # Fetch incoming dSPACE/Simulink info here
FORWARD_IP = "127.0.0.1"  # Localhost IP
FORWARD_PORT = 5006      # Destination port for Simulink Angle UDP Receive block

MEM_NAME = "shared_mem"

# --- 1. Set Up Receiver Socket ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((UDP_IP, UDP_PORT_LISTEN))
recv_sock.setblocking(False)  # Non-blocking mode

# --- 2. Set Up Forwarder Socket ---
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 60)
print(f"Fetching UDP info on   -> {UDP_IP}:{UDP_PORT_LISTEN} (Non-blocking)")
print(f"Sending Angle info to  -> {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 60 + "\n")

# --- 3. Initialize Shared Memory (32 bytes max for 4 doubles/floats) ---
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32)


def main():
    print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

    start_time = time.time()
    packet_count = 0
    last_angle = 0.0

    try:
        # Run loop for 30 seconds
        while time.time() - start_time < 30:
            try:
                packet, addr = recv_sock.recvfrom(1024)
                raw_size = len(packet)
                
                angle_val = None
                torque_val = None
                phase1_val = None
                phase2_val = None

                # Handle 16-byte payload (4 x 32-bit floats)
                if raw_size == 16:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4f', packet)
                # Handle 32-byte payload (4 x 64-bit doubles)
                elif raw_size == 32:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4d', packet)
                else:
                    print(f"[WARNING] Received unexpected packet size: {raw_size} bytes from {addr}")

                if angle_val is not None:
                    # Update memory
                    mem_data[0] = angle_val
                    mem_data[1] = torque_val
                    mem_data[2] = phase1_val
                    mem_data[3] = phase2_val

                    last_angle = float(angle_val)

                    # Forward ONLY the received angle as double to Simulink
                    angle_payload = struct.pack('<d', last_angle)
                    fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

                    packet_count += 1
                    print(f"[{packet_count:04d}] [REAL DATA ({raw_size}B)] "
                          f"Angle: {last_angle:6.2f}° | Torque: {torque_val:6.2f} Nm "
                          f"--> Forwarded to Port {FORWARD_PORT}")

            except BlockingIOError:
                # Port 5005 is idle; do nothing and continue waiting
                pass

            time.sleep(0.005)  # Fast polling rate

    except KeyboardInterrupt:
        print("\nManual stop triggered by user.")

    finally:
        print("\nCleaning up resources...")
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed cleanly.")


if __name__ == "__main__":
    main()
