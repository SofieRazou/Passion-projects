# # import socket
# # import struct
# # import time
# # import math
# # from shared_mem_manager import SManager

# # # --- Network Configuration ---
# # ANY_IP = "0.0.0.0"          # Listen on ALL network interfaces
# # UDP_PORT_LISTEN = 5005      # Fetch incoming dSPACE/Simulink info here

# # FORWARD_IP = "127.0.0.1"    # Destination port for Simulink
# # FORWARD_PORT = 5006       

# # MEM_NAME = "shared_mem"

# # # --- 1. Set Up Receiver Socket ---
# # recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# # recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# # recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

# # # CRITICAL FIX: Set a 50ms timeout instead of non-blocking mode.
# # # This lets Python wait for real incoming packets instead of instantly skipping to fallback!
# # recv_sock.settimeout(0.05) 

# # # --- 2. Set Up Forwarder Socket ---
# # fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# # fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# # print("=" * 60)
# # print(f"Listening on ALL interfaces -> Port: {UDP_PORT_LISTEN} (50ms timeout)")
# # print(f"Forwarding Angle info to     -> {FORWARD_IP}:{FORWARD_PORT}")
# # print("=" * 60 + "\n")

# # # --- 3. Initialize Shared Memory ---
# # manager = SManager()
# # # Allocating 32 bytes to handle up to 4 doubles safely
# # sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32) 


# # def main():
# #     print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

# #     start_time = time.time()
# #     packet_count = 0
# #     t = 0.0

# #     try:
# #         # Run loop for 30 seconds
# #         while time.time() - start_time < 30:
# #             angle_to_send = 0.0
# #             data_received = False

# #             # --- Step A: Wait up to 50ms for real packet from port 5005 ---
# #             try:
# #                 packet, addr = recv_sock.recvfrom(1024)
# #                 raw_size = len(packet)

# #                 angle_val = None
# #                 torque_val = None
# #                 phase1_val = None
# #                 phase2_val = None

# #                 # Support 16-byte payload (4 floats)
# #                 if raw_size == 16:
# #                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4f', packet)
# #                 # Support 32-byte payload (4 doubles)
# #                 elif raw_size == 32:
# #                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4d', packet)
# #                 else:
# #                     print(f"Warning: Unexpected packet size ({raw_size} bytes) from {addr}")

# #                 if angle_val is not None:
# #                     # Write to Shared Memory
# #                     mem_data[0] = angle_val
# #                     mem_data[1] = torque_val
# #                     mem_data[2] = phase1_val
# #                     mem_data[3] = phase2_val

# #                     angle_to_send = float(angle_val)
# #                     data_received = True

# #             except socket.timeout:
# #                 # Triggered ONLY when no packet arrives within 50ms
# #                 data_received = False

# #             # --- Step B: Fallback test signal ONLY if port 5005 timed out ---
# #             if not data_received:
# #                 angle_to_send = 45.0 * math.sin(t)  # Generates test sine wave [-45°, +45°]
# #                 t += 0.05
# #                 time.sleep(0.05)  # Pace fallback rate to ~20Hz

# #             # --- Step C: Forward angle to Simulink on port 5006 ---
# #             angle_payload = struct.pack('<d', angle_to_send)
# #             fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

# #             packet_count += 1
# #             mode_tag = "REAL DATA (5005)" if data_received else "FALLBACK SINE"

# #             print(f"[{packet_count:04d}] [{mode_tag}] Sent Angle: {angle_to_send:6.2f}° --> Port {FORWARD_PORT}")

# #     except KeyboardInterrupt:
# #         print("\nManual stop triggered by user.")

# #     finally:
# #         print("\nCleaning up resources...")
# #         recv_sock.close()
# #         fwd_sock.close()
# #         print("Sockets closed cleanly.")


# # if __name__ == "__main__":
# #     main()
# import os
# import socket
# import struct
# import time
# from shared_mem_manager import SManager

# # --- Network Configuration ---
# ANY_IP = "0.0.0.0"          # Listen on ALL network interfaces
# UDP_PORT_LISTEN = 5005      # Fetch incoming dSPACE/Simulink info here

# FORWARD_IP = "127.0.0.1"    # Destination IP for Simulink
# FORWARD_PORT = 5006         # Destination port for Simulink

# MEM_NAME = "shared_mem"

# FILE_PATH = "angle_logs.txt"
# TEMP_FILE_PATH = "angle_logs.tmp"

# # --- 1. Set Up Receiver Socket ---
# recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

# # 50ms timeout to allow fallback if dSPACE stops sending
# recv_sock.settimeout(0.05) 

# # --- 2. Set Up Forwarder Socket ---
# fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# print("=" * 60)
# print(f"Listening on ALL interfaces -> Port: {UDP_PORT_LISTEN} (50ms timeout)")
# print(f"Forwarding Angle info to     -> {FORWARD_IP}:{FORWARD_PORT}")
# print("=" * 60 + "\n")

# # --- 3. Initialize Shared Memory ---
# manager = SManager()
# # Allocating 32 bytes to handle up to 4 doubles safely
# sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32) 


# def safe_file_write(file_path, temp_path, value):
#     """Safely writes a value to a file using atomic replacement."""
#     try:
#         with open(temp_path, "w") as f:
#             f.write(f"{value}\n")
#         os.replace(temp_path, file_path)
#     except Exception as e:
#         pass


# def safe_file_read(file_path):
#     """Reads the last recorded angle from the file safely."""
#     try:
#         if os.path.exists(file_path):
#             with open(file_path, "r") as fread:
#                 data = fread.readline().strip()
#                 if data:
#                     return float(data)
#     except Exception:
#         pass
#     return 0.0  # Fallback default if file read fails


# def main():
#     print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

#     start_time = time.time()
#     packet_count = 0

#     try:
#         # Run loop for 30 seconds
#         while time.time() - start_time < 30:
#             angle_to_send = 0.0
#             data_received = False

#             # --- Step A: Wait up to 50ms for real packet from port 5005 ---
#             try:
#                 packet, addr = recv_sock.recvfrom(1024)
#                 raw_size = len(packet)

#                 angle_val = None
#                 torque_val = None
#                 phase1_val = None
#                 phase2_val = None

#                 # Support 16-byte payload (4 floats)
#                 if raw_size == 16:
#                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4f', packet)
#                 # Support 32-byte payload (4 doubles)
#                 elif raw_size == 32:
#                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4d', packet)
#                 else:
#                     print(f"Warning: Unexpected packet size ({raw_size} bytes) from {addr}")

#                 if angle_val is not None:
#                     angle_to_send = float(angle_val)
#                     data_received = True

#                     # Update Shared Memory
#                     mem_data[0] = angle_val
#                     mem_data[1] = torque_val
#                     mem_data[2] = phase1_val
#                     mem_data[3] = phase2_val

#                     # Write latest angle to file atomically
#                     safe_file_write(FILE_PATH, TEMP_FILE_PATH, angle_to_send)

#             except socket.timeout:
#                 data_received = False

#             # --- Step B: Fallback read from file ONLY if port 5005 timed out ---
#             if not data_received:
#                 angle_to_send = safe_file_read(FILE_PATH)

#             # --- Step C: Forward angle to Simulink on port 5006 ---
#             angle_payload = struct.pack('<d', angle_to_send)
#             fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

#             packet_count += 1
#             mode_tag = "REAL DATA (5005)" if data_received else "FALLBACK FILE"

#             print(f"[{packet_count:04d}] [{mode_tag}] Sent Angle: {angle_to_send:6.2f}° --> Port {FORWARD_PORT}")

#     except KeyboardInterrupt:
#         print("\nManual stop triggered by user.")

#     finally:
#         print("\nCleaning up resources...")
#         recv_sock.close()
#         fwd_sock.close()
        
#         if hasattr(manager, 'close'):
#             manager.close()
            
#         # Remove temporary file if leftover
#         if os.path.exists(TEMP_FILE_PATH):
#             try:
#                 os.remove(TEMP_FILE_PATH)
#             except OSError:
#                 pass
                
#         print("Sockets and Shared Memory closed cleanly.")


# if __name__ == "__main__":
#     main()
import socket
import struct
import time
from shared_mem_manager import SManager

# ------------------------------------------------------------------
# Network Configuration
# ------------------------------------------------------------------
ANY_IP = "127.0.0.1"
UDP_PORT_LISTEN = 5005

FORWARD_IP = "127.0.0.1"
FORWARD_PORT = 5006

MEM_NAME = "shared_mem"
FILE_PATH = "angle_logs.txt"

# ------------------------------------------------------------------
# Receiver Socket
# ------------------------------------------------------------------
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))
recv_sock.settimeout(0.05)      # Wait up to 50 ms for a packet

# ------------------------------------------------------------------
# Forward Socket
# ------------------------------------------------------------------
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 60)
print(f"Listening on {ANY_IP}:{UDP_PORT_LISTEN}")
print(f"Forwarding to {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 60)

# ------------------------------------------------------------------
# Shared Memory
# ------------------------------------------------------------------
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32)


def main():

    print("\nBridge running... Press Ctrl+C to stop.\n")

    start_time = time.time()
    packet_count = 0

    # Keep the most recent valid angle
    last_angle = 0.0

    try:

        while time.time() - start_time < 30:

            data_received = False
            angle_to_send = last_angle

            try:
                packet, addr = recv_sock.recvfrom(1024)
                raw_size = len(packet)

                if raw_size == 16:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                        "<4f", packet
                    )

                elif raw_size == 32:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                        "<4d", packet
                    )

                else:
                    print(f"Warning: Unexpected packet size ({raw_size} bytes)")
                    continue

                # Update shared memory
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val

                angle_to_send = float(angle_val)
                last_angle = angle_to_send
                data_received = True

                # Optional logging
                try:
                    with open(FILE_PATH, "w") as f:
                        f.write(str(angle_to_send))
                except OSError:
                    pass

            except socket.timeout:
                # No packet received -> keep previous angle
                angle_to_send = last_angle

            except struct.error as e:
                print(f"Packet unpack error: {e}")
                continue

            # Forward latest angle to Simulink
            try:
                payload = struct.pack("<d", angle_to_send)
                fwd_sock.sendto(payload, (FORWARD_IP, FORWARD_PORT))
            except OSError as e:
                print(f"Send error: {e}")

            packet_count += 1

            mode = "REAL DATA" if data_received else "LAST VALUE"

            print(
                f"[{packet_count:05d}] "
                f"[{mode}] "
                f"Angle = {angle_to_send:8.3f}°"
            )

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed.")


if __name__ == "__main__":
    main()
