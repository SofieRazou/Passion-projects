import socket
import time

# 1. Define the shared IP and distinct ports
IP = "127.0.0.1"
PORT_A = 5001
PORT_B = 5002

# 2. Create the UDP sockets (AF_INET = IPv4, SOCK_DGRAM = UDP)
sock_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 3. Bind the sockets to their respective ports
sock_a.bind((IP, PORT_A))
sock_b.bind((IP, PORT_B))

# 4. Set both sockets to non-blocking mode
sock_a.setblocking(False)
sock_b.setblocking(False)

print("Sockets created, bound, and set to non-blocking.\n")

# --- Communication Test ---

# Socket A sends a message to Socket B's port
message = b"Hello from Socket A!"
sock_a.sendto(message, (IP, PORT_B))
print(f"Socket A sent: '{message.decode()}' to port {PORT_B}")

# Slight pause to ensure the OS routes the local packet (optional but good practice in tests)
time.sleep(0.1) 

# Socket B attempts to read
try:
    # 1024 is the buffer size in bytes
    data, addr = sock_b.recvfrom(1024)
    print(f"Socket B received: '{data.decode()}' from {addr}")
except BlockingIOError:
    # In non-blocking mode, if no data is present, Python raises a BlockingIOError
    print("Socket B: No data available to read right now.")

# Socket A attempts to read (but no one sent it anything)
try:
    data, addr = sock_a.recvfrom(1024)
    print(f"Socket A received: '{data.decode()}' from {addr}")
except BlockingIOError:
    print("Socket A: No data available to read right now. Moving on!")
