import socket
import struct
import time

from shared_mem_manager import SManager


# ==============================
# Incoming UDP configuration
# ==============================

UDP_IP = "134.105.60.99"
UDP_PORT = 55001

PACKET_SIZE = 16                 # 4 floats = 4*4 bytes
PACKET_FORMAT = '<4f'            # little endian, 4 float32 values


# ==============================
# Outgoing UDP configuration
# ==============================

FORWARD_IP = "134.105.60.99"

FORWARD_PORT_1 = 55002           # Simulink UDP receiver 1
FORWARD_PORT_2 = 5006            # Simulink UDP receiver 2


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
print(f"Forwarding angle to:")
print(f"  -> {FORWARD_IP}:{FORWARD_PORT_1}")
print(f"  -> {FORWARD_IP}:{FORWARD_PORT_2}")
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

            # Receive UDP packet
            packet, addr = sock.recvfrom(2048)

            t = time.time() - start_time


            if len(packet) == PACKET_SIZE:

                # Decode:
                # angle, torque, phase1, phase2
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    PACKET_FORMAT,
                    packet
                )


                # ==============================
                # Send angle to two UDP ports
                # ==============================

                # Send as double (8 bytes)
                angle_payload = struct.pack(
                    '<d',
                    float(angle_val)
                )


                # Receiver 1
                forward_sock.sendto(
                    angle_payload,
                    (FORWARD_IP, FORWARD_PORT_1)
                )


                # Receiver 2
                forward_sock.sendto(
                    angle_payload,
                    (FORWARD_IP, FORWARD_PORT_2)
                )


                # ==============================
                # Write to shared memory
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
