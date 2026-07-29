import socket
import struct
import time
from shared_mem_manager import SManager

# --- Network Configuration ---
# 1. Listening configuration (dSPACE sender)
LISTEN_IP = "127.0.0.1"  # Or "0.0.0.0" / "134.105.60.99" if dSPACE is external
LISTEN_PORT = 5005

# 2. Forwarding configuration (Simulink receiver)
FORWARD_IP = "127.0.0.1"
FORWARD_PORT = 5006

# Packet specifications from dSPACE (4 floats = 16 bytes)
INCOMING_PACKET_SIZE = 16
INCOMING_FORMAT = '<4f'  # Little-endian 4 floats: angle, torque, phase1, phase2

MEM_NAME = "shared_mem"

# Setup Sockets
# Receiver Socket (dSPACE)
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.bind((LISTEN_IP, LISTEN_PORT))
recv_sock.settimeout(6)

# Forwarder Socket (Simulink)
forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Listening for dSPACE on {LISTEN_IP}:{LISTEN_PORT}...")
print(f"Forwarding Angle only to Simulink on {FORWARD_IP}:{FORWARD_PORT}...")

# Initialize Shared Memory
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=INCOMING_PACKET_SIZE)

def main():
    print("Shared memory ready. Press Ctrl+C to stop.")
    start_time = time.time()
    
    try:
        while True:
            # Receive packet from dSPACE
            packet, addr = recv_sock.recvfrom(2048)
            t = time.time() - start_time

            if len(packet) == INCOMING_PACKET_SIZE:
                # Unpack 4 floats from dSPACE
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(INCOMING_FORMAT, packet)

                # --- 1. FORWARD ANGLE TO SIMULINK (PORT 5006) ---
                # Option A: Pack as 8-byte double ('<d') - standard for Simulink UDP receive
                angle_payload = struct.pack('<d', float(angle_val))
                
                # Option B: If your Simulink UDP block expects a 4-byte float ('<f'), use this instead:
                # angle_payload = struct.pack('<f', float(angle_val))
                
                forward_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

                # --- 2. UPDATE SHARED MEMORY ---
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val

                print(f"Angle: {angle_val:.2f}° forwarded to {FORWARD_PORT} | Torque: {torque_val:.2f} Nm")

    except (KeyboardInterrupt, socket.timeout):
        print("\nExiting and closing sockets...")
    finally:
        recv_sock.close()
        forward_sock.close()

if __name__ == "__main__":
    main()
