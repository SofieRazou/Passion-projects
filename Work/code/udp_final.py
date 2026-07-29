import socket
import struct
import time

LISTEN_IP = "134.105.60.99"  # dSPACE IP
LISTEN_PORT = 5005

FORWARD_IP = "127.0.0.1"
FORWARD_PORT = 5006

PACKET_SIZE = 16
PACKET_FORMAT = '<4f'

# 1. Receiver socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))
# Set a very low timeout (10 ms) so recvfrom doesn't block execution
sock.settimeout(0.01)

# 2. Forwarder socket
forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

latest_angle = 0.0  # Store last known angle

def main():
    global latest_angle
    print("Running non-blocking UDP receiver...")
    
    while True:
        try:
            # Non-blocking attempt to read from dSPACE
            packet, addr = sock.recvfrom(2048)
            if len(packet) == PACKET_SIZE:
                angle_val, torque, p1, p2 = struct.unpack(PACKET_FORMAT, packet)
                latest_angle = angle_val
                print(f"Received from dSPACE: Angle = {latest_angle:.2f}°")
                
        except socket.timeout:
            # No packet arrived within 10ms; continue running without blocking
            pass
        except KeyboardInterrupt:
            break

        # Always attempt to forward the latest available angle to Simulink
        angle_payload = struct.pack('<d', float(latest_angle))
        forward_sock.sendto(angle_payload, (FORWARD_IP, FORWARD_PORT))

        time.sleep(0.005)  # Small sleep to regulate send rate (~200 Hz)

    sock.close()
    forward_sock.close()

if __name__ == "__main__":
    main()
