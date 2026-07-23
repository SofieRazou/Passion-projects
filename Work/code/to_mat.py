import mmap
import os
import struct
import time
import math

FILE_PATH = "shared_data.bin"

# Layout:
# uint64 sequence counter = 8 bytes
# double x                = 8 bytes
# double y                = 8 bytes
FILE_SIZE = 24

# Create the shared file once
if not os.path.exists(FILE_PATH):
    with open(FILE_PATH, "wb") as file:
        file.write(b"\x00" * FILE_SIZE)

with open(FILE_PATH, "r+b") as file:
    shared_memory = mmap.mmap(file.fileno(), FILE_SIZE)

    sequence = 0

    try:
        while True:
            current_time = time.perf_counter()

            x = math.sin(current_time)
            y = math.cos(current_time)

            # Odd number means Python is currently writing
            sequence += 1
            shared_memory[0:8] = struct.pack("<Q", sequence)

            # Write x and y
            shared_memory[8:24] = struct.pack("<dd", x, y)

            # Even number means writing has finished
            sequence += 1
            shared_memory[0:8] = struct.pack("<Q", sequence)

            print(f"x={x:.4f}, y={y:.4f}")

            time.sleep(0.01)  # approximately 100 Hz

    except KeyboardInterrupt:
        print("Transmission stopped.")

    finally:
        shared_memory.close()
