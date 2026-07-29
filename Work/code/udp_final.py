import socket
import struct
import time
import sys
from shared_mem_manager import SManager

# --- Incoming Network Configuration ---
UDP_IP = "134.105.60.99"
UDP_PORT = 55001

# --- Outgoing Network Configuration (Dual Port Forwarding) ---
FORWARD_IP = "134.105.60.99"
FORWARD_PORT_1 = 55002  # First target port (e.g., Simulink Receive Block 1)
FORWARD_PORT_2 = 55003  # Second target port (e.g., Simulink Receive Block 2 / Haptic UI)
TARGET_PORTS = [FORWARD_PORT_1, FORWARD_PORT_2]

REDUNDANCY_BURST = 1  # Set > 1 if packet loss over network is expected

PACKET_SIZE = 16
PACKET_FORMAT = '<4f'  # Incoming payload format (4 floats = 16 bytes)

MEM_NAME = "shared_mem"

# 1. Receiver socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(6)

# 2. Forwarder socket
forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Listening for incoming UDP packets on {UDP_IP}:{UDP_PORT}...")
print(f"Forwarding live Angle to ports {TARGET_PORTS} on IP {FORWARD_IP}...")

manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=PACKET_SIZE)

time_arr = []

def main(): 
    print("Shared memory created. Press Ctrl+C to exit.")

    start_time = time.time()
    sequence_id = 0

    try:
        while time.time() - start_time < 30:
            packet, addr = sock.recvfrom(2048)
            t = time.time() - start_time
            
            if len(packet) == PACKET_SIZE:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(PACKET_FORMAT, packet)

                # --- 1. PACK ANGLE PAYLOAD FOR FORWARDING ---
                # Option A: Standard double precision float (8 bytes)
                angle_payload = struct.pack('<d', float(angle_val))
                
                # Option B: Double precision float with sequence ID (12 bytes)
                # angle_payload = struct.pack('>Id', sequence_id, float(angle_val))

                # --- 2. RELIABLY FORWARD TO MULTIPLE PORTS ---
                for port in TARGET_PORTS:
                    destination = (FORWARD_IP, port)
                    for _ in range(REDUNDANCY_BURST):
                        forward_sock.sendto(angle_payload, destination)

                # --- 3. WRITE TO SHARED MEMORY ---
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val
                time_arr.append(t)
                
                print(f"LIVE Angle: {angle_val:.2f}° | Forwarded to Ports {TARGET_PORTS} | Torque: {torque_val:.2f} Nm")
                sequence_id += 1
            
    except (KeyboardInterrupt, socket.timeout):
        print("Exiting execution...")
    finally:
        print("Closing network sockets...")
        sock.close()
        forward_sock.close()

if __name__ == "__main__":
    main()
