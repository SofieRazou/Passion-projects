import socket
import struct
import time
import math
from shared_mem_manager import SManager

# --- Network Configuration ---
UDP_IP = "127.0.0.1"      # Localhost IP
UDP_PORT_LISTEN = 5005   # Input port (dSPACE / External Source)
FORWARD_IP = "127.0.0.1"  # Target IP for Simulink
FORWARD_PORT = 5006      # Output port for Simulink UDP Receive block

PACKET_SIZE = 16
PACKET_FORMAT = '<4f'     # 4 Little-Endian floats

MEM_NAME = "shared_mem"

# --- 1. Receiver Socket (Port 5005) ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((UDP_IP, UDP_PORT_LISTEN))
recv_sock.setblocking(False)  # Non-blocking mode

# --- 2. Forwarder Socket (Port 5006) ---
fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fwd_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

print("=" * 65)
print(f"1. Listening for 4x Float packets on -> {UDP_IP}:{UDP_PORT_LISTEN}")
print(f"2. Forwarding Angle to Simulink on  -> {FORWARD_IP}:{FORWARD_PORT}")
print("=" * 65 + "\n")

# --- 3. Initialize Shared Memory ---
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)


def main():
    print("Relay Active. Streaming to Simulink... (Press Ctrl+C to stop)\n")

    start_time = time.time()
    t = 0.0
    packet_count = 0

    try:
        while True:
            angle_to_send = 0.0
            data_received = False

            # --- Step A: Try to read real data from Port 5005 ---
            try:
                packet, addr = recv_sock.recvfrom(1024)
                if len(packet) == PACKET_SIZE:
                    angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

                    # Store in shared memory
                    mem_data[0] = angle_val
                    mem_data[1] = torque_val
                    mem_data[2] = phase1_val
                    mem_data[3] = phase2_val

                    angle_to_send = float(angle_val)
                    data_received = True

            except BlockingIOError:
                # No data on port 5005 yet
                data_received = False

            # --- Step B: Fallback Dummy Signal for Testing Simulink ---
            if not data_received:
                # Generates a smooth sine wave angle (-45° to +45°) if port 5005 is silent
                angle_to_send = 45.0 * math.sin(t)

            # --- Step C: ALWAYS send to Simulink on Port 5006 ---
            angle_payload = struct.pack('<d', angle_to_send)
            fwd_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

            packet_count += 1
            mode_str = "REAL DATA (5005)" if data_received else "TEST SINE WAVE"
            print(f"[{packet_count:04d}] [{mode_str}] Sent Angle: {angle_to_send:6.2f}° -> Port {FORWARD_PORT}")

            t += 0.05
            time.sleep(0.05)  # 20 Hz loop rate matching Simulink sample time

    except KeyboardInterrupt:
        print("\nManual stop triggered.")

    finally:
        recv_sock.close()
        fwd_sock.close()
        print("Sockets closed.")


if __name__ == "__main__":
    main()
