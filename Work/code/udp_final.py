import socket
import struct
import time

from shared_mem_manager import SManager


# ==========================================================
# Incoming UDP: dSPACE -> Python
# ==========================================================

UDP_IP = "134.105.60.99"
UDP_PORT = 55001

PACKET_SIZE = 16              # 4 x float32 = 16 bytes
PACKET_FORMAT = '<4f'         # angle, torque, phase1, phase2


# ==========================================================
# Outgoing UDP: Python -> Simulink
# ==========================================================

# If Simulink is on the SAME PC as Python:
# use "127.0.0.1"

# If Simulink is on another PC:
# use the Simulink PC IP address

FORWARD_IP = "134.105.60.99"

FORWARD_PORT = 5006           # Simulink UDP Receive port


# ==========================================================
# Shared memory
# ==========================================================

MEM_NAME = "shared_mem"

# 4 double values:
# angle
# torque
# phase1
# phase2

MEM_SIZE = 4 * 8               # 32 bytes


# ==========================================================
# Create incoming UDP socket
# ==========================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

sock.bind(
    (UDP_IP, UDP_PORT)
)

sock.settimeout(6)


print("======================================")
print("Python UDP bridge started")
print("======================================")
print(f"Listening for dSPACE:")
print(f"  IP   : {UDP_IP}")
print(f"  PORT : {UDP_PORT}")
print("")
print(f"Forwarding angle to Simulink:")
print(f"  IP   : {FORWARD_IP}")
print(f"  PORT : {FORWARD_PORT}")
print("======================================")


# ==========================================================
# Create outgoing UDP socket
# ==========================================================

forward_sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)


# ==========================================================
# Create shared memory
# ==========================================================

manager = SManager()

sm, mem_data = manager.create_mem(
    mem_name=MEM_NAME,
    size=MEM_SIZE
)


print("Shared memory created successfully")
print("Waiting for dSPACE packets...")
print("")


# ==========================================================
# Main loop
# ==========================================================

def main():

    start_time = time.time()

    packet_counter = 0


    try:

        while True:

            # ----------------------------------------------
            # Receive packet from dSPACE
            # ----------------------------------------------

            packet, addr = sock.recvfrom(2048)

            packet_counter += 1


            print("--------------------------------------")
            print(f"Packet number: {packet_counter}")
            print(f"Received from: {addr}")
            print(f"Packet size : {len(packet)} bytes")


            # Check packet size

            if len(packet) != PACKET_SIZE:

                print(
                    "WARNING: Wrong packet size!"
                )

                print(
                    f"Expected {PACKET_SIZE}, got {len(packet)}"
                )

                continue



            # ----------------------------------------------
            # Decode dSPACE packet
            # ----------------------------------------------

            angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                PACKET_FORMAT,
                packet
            )


            print("Decoded values:")
            print(f"  Angle  : {angle_val:.6f}")
            print(f"  Torque : {torque_val:.6f}")
            print(f"  Phase1 : {phase1_val:.6f}")
            print(f"  Phase2 : {phase2_val:.6f}")



            # ----------------------------------------------
            # Forward ONLY angle to Simulink
            # ----------------------------------------------

            # Python sends:
            # double = 8 bytes
            # little endian

            angle_payload = struct.pack(
                '<d',
                float(angle_val)
            )


            bytes_sent = forward_sock.sendto(
                angle_payload,
                (
                    FORWARD_IP,
                    FORWARD_PORT
                )
            )


            print("Forwarding:")
            print(f"  Sent bytes : {bytes_sent}")
            print(f"  Destination: {FORWARD_IP}:{FORWARD_PORT}")



            # ----------------------------------------------
            # Write to shared memory
            # ----------------------------------------------

            mem_data[0] = angle_val
            mem_data[1] = torque_val
            mem_data[2] = phase1_val
            mem_data[3] = phase2_val


            print("Shared memory updated")
            print("--------------------------------------")



    except socket.timeout:

        print("")
        print("ERROR: No UDP packet received for 6 seconds")
        print("Check dSPACE -> Python connection")


    except KeyboardInterrupt:

        print("")
        print("Stopped manually")


    except Exception as e:

        print("")
        print("UNEXPECTED ERROR:")
        print(e)


    finally:

        print("")
        print("Closing sockets...")

        sock.close()
        forward_sock.close()



if __name__ == "__main__":
    main()
