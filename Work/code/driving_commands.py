import math
import mmap
import os
import struct
import time

FILE_PATH = r"C:\Users\javot\Desktop\sofia_code\shared_data.bin"

# Memory layout:
# Bytes 0-7:   uint64 sequence counter
# Bytes 8-15:  double steering command
# Bytes 16-23: double heading command
FILE_SIZE = 24

SAMPLE_PERIOD = 0.01  # 100 Hz
DURATION = 30.0       # seconds

# Create or reset the shared-memory file
with open(FILE_PATH, "wb") as file:
    file.write(b"\x00" * FILE_SIZE)

with open(FILE_PATH, "r+b") as file:
    shared_memory = mmap.mmap(
        file.fileno(),
        FILE_SIZE,
        access=mmap.ACCESS_WRITE
    )

    sequence = 0
    start_time = time.perf_counter()
    next_sample_time = start_time

    try:
        while time.perf_counter() - start_time < DURATION:
            current_time = time.perf_counter()
            elapsed_time = current_time - start_time

            # Example commands
            # Replace these with your real steering and heading commands
            delta = 0.05 * math.sin(0.5 * elapsed_time)
            theta_command = 0.0

            # Odd sequence: Python is writing
            sequence += 1
            shared_memory.seek(0)
            shared_memory.write(struct.pack("<Q", sequence))

            # Write the two double commands
            shared_memory.seek(8)
            shared_memory.write(
                struct.pack(
                    "<dd",
                    float(delta),
                    float(theta_command)
                )
            )

            # Even sequence: writing is complete
            sequence += 1
            shared_memory.seek(0)
            shared_memory.write(struct.pack("<Q", sequence))

            shared_memory.flush()

            print(
                "sequence = {}, delta = {:.6f}, theta = {:.6f}".format(
                    sequence,
                    delta,
                    theta_command
                )
            )

            # Maintain approximately constant sampling frequency
            next_sample_time += SAMPLE_PERIOD
            remaining_time = next_sample_time - time.perf_counter()

            if remaining_time > 0:
                time.sleep(remaining_time)
            else:
                next_sample_time = time.perf_counter()

    except KeyboardInterrupt:
        print("Transmission stopped by user.")

    finally:
        shared_memory.close()

print("Python transmission finished.")
