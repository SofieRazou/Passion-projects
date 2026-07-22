import socket
import time

UDP_IP = "127.0.0.1"      # Same PC
UDP_PORT = 50000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

counter = 0

while True:
    message = f"HELLO FROM DSPACE {counter}"

    sock.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))

    print("Sent:", message)

    counter += 1

    time.sleep(1)
