# import socket
# import struct
# import time
# import math
# from shared_mem_manager import SManager

# # --- Network Configuration ---
# ANY_IP = "0.0.0.0"          # Listen on ALL network interfaces
# UDP_PORT_LISTEN = 5005      # Fetch incoming dSPACE/Simulink info here

# FORWARD_IP = "127.0.0.1"    # Destination port for Simulink
# FORWARD_PORT = 5006       

# MEM_NAME = "shared_mem"

# # --- 1. Set Up Receiver Socket ---
# recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

# # CRITICAL FIX: Set a 50ms timeout instead of non-blocking mode.
# # This lets Python wait for real incoming packets instead of instantly skipping to fallback!
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


# def main():
#     print("Shared memory allocated. Relaying data (Press Ctrl+C to stop)...\n")

#     start_time = time.time()
#     packet_count = 0
#     t = 0.0

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
#                     # Write to Shared Memory
#                     mem_data[0] = angle_val
#                     mem_data[1] = torque_val
#                     mem_data[2] = phase1_val
#                     mem_data[3] = phase2_val

#                     angle_to_send = float(angle_val)
#                     data_received = True

#             except socket.timeout:
#                 # Triggered ONLY when no packet arrives within 50ms
#                 data_received = False

#             # --- Step B: Fallback test signal ONLY if port 5005 timed out ---
#             if not data_received:
#                 angle_to_send = 45.0 * math.sin(t)  # Generates test sine wave [-45°, +45°]
#                 t += 0.05
#                 time.sleep(0.05)  # Pace fallback rate to ~20Hz

#             # --- Step C: Forward angle to Simulink on port 5006 ---
#             angle_payload = struct.pack('<d', angle_to_send)
#             fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

#             packet_count += 1
#             mode_tag = "REAL DATA (5005)" if data_received else "FALLBACK SINE"

#             print(f"[{packet_count:04d}] [{mode_tag}] Sent Angle: {angle_to_send:6.2f}° --> Port {FORWARD_PORT}")

#     except KeyboardInterrupt:
#         print("\nManual stop triggered by user.")

#     finally:
#         print("\nCleaning up resources...")
#         recv_sock.close()
#         fwd_sock.close()
#         print("Sockets closed cleanly.")


# if __name__ == "__main__":
#     main()
import queue
import socket
import struct
import threading
import time
from shared_mem_manager import SManager

# --- Network Configuration ---
ANY_IP = "0.0.0.0"
UDP_PORT_LISTEN = 5005

FORWARD_IP = "127.0.0.1"
FORWARD_PORT = 5006

MEM_NAME = "shared_mem"

# --- Thread-Safe Queue ---
# Holds raw UDP packets ready for processing
packet_queue = queue.Queue(maxsize=1000)
stop_event = threading.Event()

# --- Sockets ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((ANY_IP, UDP_PORT_LISTEN))

fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def udp_receiver_thread():
    """Producer thread: Continuously receives UDP packets and pushes them to queue."""
    while not stop_event.is_set():
        try:
            recv_sock.settimeout(1.0)
            packet, addr = recv_sock.recvfrom(1024)
            # Push packet into queue without blocking the network interface
            packet_queue.put_nowait(packet)
        except socket.timeout:
            continue
        except queue.Full:
            # Drop oldest item if processing thread falls far behind
            try:
                packet_queue.get_nowait()
                packet_queue.put_nowait(packet)
            except queue.Empty:
                pass


def main():
    manager = SManager()
    sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32)

    # Start network receiver thread
    receiver_thread = threading.Thread(target=udp_receiver_thread, daemon=True)
    receiver_thread.start()

    print(
        f"Listening on {UDP_PORT_LISTEN} -> Forwarding buffered data to {FORWARD_PORT}\n"
    )

    packet_count = 0

    try:
        while True:
            try:
                # Consumer: Fetch packet from buffer queue (blocks up to 1 second)
                packet = packet_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            raw_size = len(packet)
            angle_val = None

            # Unpack based on size
            if raw_size == 16:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    "<4f", packet
                )
            elif raw_size == 32:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    "<4d", packet
                )
            else:
                packet_queue.task_done()
                continue

            # Update Shared Memory
            mem_data[0] = angle_val
            mem_data[1] = torque_val
            mem_data[2] = phase1_val
            mem_data[3] = phase2_val

            # Forward Angle to Simulink
            angle_payload = struct.pack("<d", float(angle_val))
            fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

            packet_queue.task_done()
            packet_count += 1

            if packet_count % 100 == 0:
                print(
                    f"[{packet_count:06d}] Relayed Angle: {angle_val:6.2f}° (Queue Depth: {packet_queue.qsize()})"
                )

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stop_event.set()
        receiver_thread.join(timeout=2.0)

        recv_sock.close()
        fwd_sock.close()

        if hasattr(manager, "close"):
            manager.close()
        print("Resources cleaned up cleanly.")


if __name__ == "__main__":
    main()
