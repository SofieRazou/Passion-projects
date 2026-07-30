import os
import socket
import struct
import time
from shared_mem_manager import SManager

# --- Configuration ---
LISTEN_IP = "0.0.0.0"
UDP_PORT_LISTEN = 5005
MEM_NAME = "shared_mem"

ANGLE_FILE = "latest_angle.txt"
TEMP_FILE = "latest_angle.tmp"

# --- Socket Setup ---
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind((LISTEN_IP, UDP_PORT_LISTEN))

# --- Shared Memory ---
manager = SManager()
sm, mem_data = manager.create_mem(mem_name=MEM_NAME, size=32)

print("=" * 60)
print(f"Listening on port {UDP_PORT_LISTEN}")
print(f"Writing incoming angle to file: '{ANGLE_FILE}'")
print("=" * 60 + "\n")


def write_angle_atomically(angle_value):
    """Writes the angle to a temp file first, then safely replaces the target file."""
    try:
        with open(TEMP_FILE, "w") as f:
            f.write(f"{angle_value:.4f}")
        # Atomic replace prevents MATLAB from reading a half-written file
        os.replace(TEMP_FILE, ANGLE_FILE)
    except Exception as e:
        pass


def main():
    packet_count = 0
    try:
        while True:
            packet, addr = recv_sock.recvfrom(1024)
            raw_size = len(packet)

            angle_val = None
            torque_val = None
            phase1_val = None
            phase2_val = None

            # Unpack payload based on byte size
            if raw_size == 16:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    "<4f", packet
                )
            elif raw_size == 32:
                angle_val, torque_val, phase1_val, phase2_val = struct.unpack(
                    "<4d", packet
                )
            elif raw_size == 4:
                angle_val = struct.unpack("<f", packet)[0]
            elif raw_size == 8:
                angle_val = struct.unpack("<d", packet)[0]
            else:
                continue

            # Update Shared Memory
            if torque_val is not None:
                mem_data[0] = angle_val
                mem_data[1] = torque_val
                mem_data[2] = phase1_val
                mem_data[3] = phase2_val

            # Write angle to file for MATLAB
            write_angle_atomically(angle_val)

            packet_count += 1
            if packet_count % 100 == 0:
                print(
                    f"[{packet_count:06d}] Written Angle to File: {angle_val:6.2f}°"
                )

    except KeyboardInterrupt:
        print("\nStopping script...")
    finally:
        recv_sock.close()
        if hasattr(manager, "close"):
            manager.close()
        # Clean up temporary files
        for fname in [TEMP_FILE, ANGLE_FILE]:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except OSError:
                    pass
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
