import socket
import struct
import time
import math
from shared_mem_manager import SManager

# --- Network Configuration ---
ANY_IP = "127.0.0.1"          # Listen on ALL network interfaces
UDP_PORT_LISTEN = 5005      # Fetch incoming dSPACE/Simulink info here

FORWARD_IP = "127.0.0.1"    # Destination port for Simulink
FORWARD_PORT = 5006       

MEM_NAME = "shared_mem"

FILE_PATH = "angle_logs.txt"

# --- 1. Set Up Receiver Socket ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

# CRITICAL FIX: Set a 50ms timeout instead of non-blocking mode.
# This lets Python wait for real incoming packets instead of instantly skipping to fallback!
recv_sock.settimeout(0.05) 

# --- 2. Set Up Forwarder Socket ---
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 60)
print(f"Listening on ALL interfaces -> Port: {UDP_PORT_LISTEN} (50ms timeout)")
print(f"Forwarding Angle info to     -> {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 60 + "\n")

# --- 3. Initialize Shared Memory ---
manager = SManager()
# Allocating 32 bytes to handle up to 4 doubles safely
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32) 


def main():
    print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

    start_time = time.time()
    packet_count = 0
    t = 0.0

    try:
        # Run loop for 30 seconds
        while time.time() - start_time < 30:
            data_received = False
            angle_to_send = 0.0

            try:
                packet, addr = recv_sock.recvfrom(1024)
                raw_size = len(packet)

                if raw_size == 16:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack("<4f", packet)
                elif raw_size == 32:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack("<4d", packet)
                else:
                    print(f"Unexpected packet size: {raw_size}")
                continue

                # Store in shared memory
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val

                angle_to_send = float(angle_val)
                data_received = True

            except socket.timeout:
                # No packet received -> use previous value
                try:
                    with open(FILE_PATH, "r") as f:
                        angle_to_send = float(f.readline().strip())
                except (FileNotFoundError, ValueError):
                    angle_to_send = 0.0

        # Save latest valid angle
        try:
            with open(FILE_PATH, "w") as f:
                f.write(str(angle_to_send))
        except OSError:
            pass

        # Forward to Simulink
        payload = struct.pack("<d", angle_to_send)
        fwd_sock.sendto(payload, (FORWARD_IP, FORWARD_PORT))

        packet_count += 1
        mode = "REAL DATA" if data_received else "FALLBACK"

        print(
            f"[{packet_count:04d}] [{mode}] "
            f"Angle = {angle_to_send:7.3f}°"
        )

    except KeyboardInterrupt:
        print("\nManual stop triggered by user.")

    finally:
        print("\nCleaning up resources...")
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed cleanly.")


if __name__ == "__main__":
    main()





# import socket
# import struct
# import time
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


# def main():
#     print("Shared memory allocated. Streaming started (Press Ctrl+C to stop)...\n")

#     start_time = time.time()
#     packet_count = 0

#     try:
#         # Run loop for 30 seconds
#         while time.time() - start_time < 30:
#             try:
#                 packet, addr = recv_sock.recvfrom(1024)
                
#                 if len(packet) == PACKET_SIZE:
#                     # Unpack incoming 4 floats
#                     angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

#                     # --- Write to Shared Memory ---
#                     mem_data[0] = angle_val
#                     mem_data[1] = torque_val
#                     mem_data[2] = phase1_val
#                     mem_data[3] = phase2_val

#                     # --- Forward ONLY Angle Value to Simulink (as double '<d') ---
#                     angle_payload = struct.pack('<d', float(angle_val))
#                     fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

#                     packet_count += 1
                    
#                     # Console confirmation
#                     print(f"[{packet_count:04d}] Fetched data from port {UDP_PORT_LISTEN} | "
#                           f"Angle: {angle_val:6.2f}° | Torque: {torque_val:6.2f} Nm "
#                           f"--> [Angle forwarded to port {FORWARD_PORT}]")

#             except BlockingIOError:
#                 # Expected in non-blocking mode when no data is in the socket buffer
#                 pass

#             time.sleep(0.005)  # Prevents high CPU usage

#     except KeyboardInterrupt:
#         print("\nManual stop triggered by user.")

#     finally:
#         print("\nCleaning up resources...")
#         recv_sock.close()
#         fwd_sock.close()
#         print("Sockets closed cleanly.")


# if __name__ == "__main__":
#     main()
import socket
import struct
import time
import math
from shared_mem_manager import SManager

# --- Network Configuration ---
ANY_IP = "127.0.0.1"          # Listen on ALL network interfaces
UDP_PORT_LISTEN = 5005      # Fetch incoming dSPACE/Simulink info here

FORWARD_IP = "127.0.0.1"    # Destination port for Simulink
FORWARD_PORT = 5006       

MEM_NAME = "shared_mem"

FILE_PATH = "angle_logs.txt"

# --- 1. Set Up Receiver Socket ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

# CRITICAL FIX: Set a 50ms timeout instead of non-blocking mode.
# This lets Python wait for real incoming packets instead of instantly skipping to fallback!
recv_sock.settimeout(0.05) 

# --- 2. Set Up Forwarder Socket ---
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 60)
print(f"Listening on ALL interfaces -> Port: {UDP_PORT_LISTEN} (50ms timeout)")
print(f"Forwarding Angle info to     -> {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 60 + "\n")

# --- 3. Initialize Shared Memory ---
manager = SManager()
# Allocating 32 bytes to handle up to 4 doubles safely
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32) 


def main():
    print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

    start_time = time.time()
    packet_count = 0
    t = 0.0

    try:
        # Run loop for 30 seconds
        while time.time() - start_time < 30:
            angle_to_send = 0.0
            data_received = False

            # --- Step A: Wait up to 50ms for real packet from port 5005 ---
            try:
                packet, addr = recv_sock.recvfrom(1024)
                raw_size = len(packet)

                angle_val = None
                torque_val = None
                phase1_val = None
                phase2_val = None

                # Support 16-byte payload (4 floats)
                if raw_size == 16:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4f', packet)
                # Support 32-byte payload (4 doubles)
                elif raw_size == 32:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack('<4d', packet)
                else:
                    print(f"Warning: Unexpected packet size ({raw_size} bytes) from {addr}")

                if angle_val is not None:
                    # Write to Shared Memory
                    with open(FILE_PATH, "w") as f:
                        f.write(str(angle_val))
                    mem_data[0] = angle_val
                    mem_data[1] = torque_val
                    mem_data[2] = phase1_val
                    mem_data[3] = phase2_val

                    angle_to_send = float(angle_val)
                    data_received = True

            except socket.timeout:
                # Triggered ONLY when no packet arrives within 50ms
                data_received = False

            # --- Step B: Fallback test signal ONLY if port 5005 timed out ---
            if not data_received:
                # angle_to_send = 45.0 * math.sin(t)  # Generates test sine wave [-45°, +45°]
                # t += 0.05
                # time.sleep(0.05)  # Pace fallback rate to ~20Hz
                with open(FILE_PATH, "r") as fread:
                    angle_data = fread.readline().strip()
                    angle_send  = float(angle_data)
    
            # --- Step C: Forward angle to Simulink on port 5006 ---
            angle_payload = struct.pack('<d', angle_send)
            fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

            packet_count += 1
            mode_tag = "REAL DATA (5005)" if data_received else "FALLBACK SINE"

            print(f"[{packet_count:04d}] [{mode_tag}] Sent Angle: {angle_to_send:6.2f}° --> Port {FORWARD_PORT}")

    except KeyboardInterrupt:
        print("\nManual stop triggered by user.")

    finally:
        print("\nCleaning up resources...")
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed cleanly.")


if __name__ == "__main__":
    main()
