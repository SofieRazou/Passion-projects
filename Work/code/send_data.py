import socket
import struct
import time

# --- Network Configuration ---
UDP_IP = "127.0.0.1"  # Localhost (same computer as Simulink)
UDP_PORT = 5005        # Port matching Simulink UDP Receive block

# --- Simulation Settings ---
dt = 0.01              # 100 Hz sampling period (seconds)
duration = 20.0        # Total run time in seconds

# Create UDP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Streaming X and Delta to {UDP_IP}:{UDP_PORT}...")

start_time = time.perf_counter()
next_step = start_time

try:
    while time.perf_counter() - start_time < duration:
        elapsed_time = time.perf_counter() - start_time
        
        # --- Define Example Inputs ---
        # Forward position (X advancing at speed)
        x = 30.0 * elapsed_time  
        
        # Wobbling steering angle (Delta oscillating in radians)
        delta = 0.1 * math.sin(2.0 * elapsed_time)
        
        # --- Pack Data ---
        # 'dd' packs two doubles (8 bytes each = 16 bytes total)
        payload = struct.pack('<dd', float(x), float(delta))
        
        # Send packet
        sock.sendto(payload, (UDP_IP, UDP_PORT))
        
        print(f"Sent -> X: {x:.2f} m, Delta: {delta:.4f} rad")
        
        # Maintain exact 100 Hz timing
        next_step += dt
        sleep_time = next_step - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    sock.close()
    print("Socket closed.")
  
