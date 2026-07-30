import socket
import threading
import time

# 1. Configuration (using higher ports to avoid Windows WinError 10013)
IP = "127.0.0.1"
PORT_A = 55001
PORT_B = 55002

# 2. Setup Sockets
sock_a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Allow immediate port reuse
sock_a.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock_b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

sock_a.bind((IP, PORT_A))
sock_b.bind((IP, PORT_B))

# Flag to control the listening loop in threads
running = True

# 3. Receiver function to run in a background thread
def listen_on_socket(sock, name):
    # Set a timeout so the thread can periodically check if 'running' is False
    sock.settimeout(1.0) 
    
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"\n[{name}] Received: '{data.decode()}' from {addr}")
        except socket.timeout:
            # Expected if no data arrived during the timeout period
            continue
        except Exception as e:
            if running:
                print(f"[{name}] Error: {e}")
            break

# 4. Start background listening threads
thread_a = threading.Thread(target=listen_on_socket, args=(sock_a, "Socket A Receiver"), daemon=True)
thread_b = threading.Thread(target=listen_on_socket, args=(sock_b, "Socket B Receiver"), daemon=True)

thread_a.start()
thread_b.start()

print("Receiving threads started. Sending messages simultaneously...\n")

# 5. Main Thread: Send messages in any order at any time
try:
    # A sends to B
    sock_a.sendto(b"Hello B, this is A!", (IP, PORT_B))
    
    # B sends to A
    sock_b.sendto(b"Hey A, got your message!", (IP, PORT_A))

    # Send rapid messages simultaneously
    for i in range(3):
        sock_a.sendto(f"Packet {i} from A".encode(), (IP, PORT_B))
        sock_b.sendto(f"Packet {i} from B".encode(), (IP, PORT_A))
        time.sleep(0.2)

    # Let threads catch final messages
    time.sleep(1)

finally:
    # Cleanup
    running = False
    thread_a.join()
    thread_b.join()
    sock_a.close()
    sock_b.close()
    print("\nSockets closed cleanly.")
