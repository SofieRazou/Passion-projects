import socket
import struct
import time

from shared_mem_manager import SManager


# ==============================
# Incoming UDP configuration
# ==============================

UDP_IP = "134.105.60.99"
UDP_PORT = 55001

PACKET_SIZE = 16                 # 4 floats = 16 bytes
PACKET_FORMAT = '<4f'            # little endian: angle, torque, phase1, phase2


# ==============================
# Outgoing UDP configuration
# ==============================

FORWARD_IP = "134.105.60.99"     # Use "127.0.0.1" if Simulink is on same PC
FORWARD_PORT = 5006              # Simulink UDP Receive port


# ==============================
# Shared memory configuration
# ==============================

MEM_NAME = "shared_mem"

# 4 double values:
# angle, torque, phase1, phase2
MEM_SIZE = 4 * 8                  # 32 bytes


# ==============================
# Create receiving UDP socket
# ==============================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))

sock.settimeout(6)


print("--------------------------------")
print("UDP receiver started")
print(f"Listening on {UDP_IP}:{UDP_PORT}")
print(f"Forwarding angle to {FORWARD_IP}:{FORWARD_PORT}")
print("--------------------------------")


# ==============================
# Create forwarding socket
# ==============================

forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# ==============================
# Create shared memory
# ==============================

manager = SManager()

sm, mem_data = manager.create_mem(
    mem_name=MEM_NAME,
    size=MEM_SIZE
)


# ==============================
# Main loop
# ==============================

def main():

    print("Shared memory created. Running...")

    start_time = time.time()

    try:

        while time.time() - start_time < 30:

            # Receive packet from dSPACE/Simulink
            packet, addr = sock.recvfrom(2048)

            t = time.time() - start_time


            if len(packet) == PACKET_SIZE:

                # Decode incoming packet
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    PACKET_FORMAT,
                    packet
                )


                # ==============================
                # Forward ONLY angle to Simulink
                # ==============================

                # Send angle as 8-byte double
                angle_payload = struct.pack(
                    '<d',
                    float(angle_val)
                )

                forward_sock.sendto(
                    angle_payload,
                    (FORWARD_IP, FORWARD_PORT)
                )


                # ==============================
                # Write values to shared memory
                # ==============================

                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val


                print(
                    f"Angle: {angle_val:.3f} deg | "
                    f"Torque: {torque_val:.3f} Nm | "
                    f"Phase1: {phase1_val:.3f} A | "
                    f"Phase2: {phase2_val:.3f} A"
                )


    except socket.timeout:

        print("UDP timeout")

    except KeyboardInterrupt:

        print("Stopped by user")


    finally:

        print("Closing sockets...")

        sock.close()
        forward_sock.close()



if __name__ == "__main__":
    main()
