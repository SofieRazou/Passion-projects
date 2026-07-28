import socket
import time
import struct

# UDP destination
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Start time
t0 = time.time()

try:
    while True:
        # Elapsed time (seconds)
        t = time.time() - t0

        # Angle = 0.1*t + 2
        angle = 0.1 * t + 2.0

        # Pack as a double (8 bytes)
        data = struct.pack('d', angle)

        # Send
        sock.sendto(data, (UDP_IP, UDP_PORT))

        print(f"t = {t:.3f} s, angle = {angle:.3f}")

        # 100 Hz update rate
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Stopped.")

finally:
    sock.close()
