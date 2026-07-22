import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 50000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Listening...")

try:
    while True:
        data, addr = sock.recvfrom(1024)

        print("Received:", data.decode("utf-8"))

except KeyboardInterrupt:
        print("Exciting with Ctrl+C...")