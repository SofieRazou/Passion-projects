import math
import mmap
import os
import struct
import time

FILE_PATH = r"C:\Users\javot\Desktop\sofia_code\shared_data.bin"

FILE_SIZE = 24
SAMPLE_PERIOD = 0.01
DURATION = 30.0

# Ensure the destination folder exists
folder = os.path.dirname(FILE_PATH)

if not os.path.isdir(folder):
    raise FileNotFoundError(
        "Folder does not exist: {}".format(folder)
    )

# Create the binary file with exactly 24 bytes
with open(FILE_PATH, "w+b") as file:
    file.truncate(FILE_SIZE)
    file.flush()

    # Map the entire file
    shared_memory = mmap.mmap(
        file.fileno(),
        length=0,
        access=mmap.ACCESS_WRITE
    )

    sequence = 0
    start_time = time.perf_counter()
    next_sample_time = start_time

    try:
        while time.perf_counter() - start_time < DURATION:
            elapsed_time = time.perf_counter() - start_time

            # Example commands
            # Replace these with your actual values
            delta = 0.05 * math.sin(0.5 * elapsed_time)
            theta_command = 0.0

            # Odd sequence means writing is in progress
            sequence += 1

            shared_memory.seek(0)
            shared_memory.write(
                struct.pack("<Q", sequence)
            )

            # Write two doubles
            shared_memory.seek(8)
            shared_memory.write(
                struct.pack(
                    "<dd",
                    float(delta),
                    float(theta_command)
                )
            )

            # Even sequence means writing is complete
            sequence += 1

            shared_memory.seek(0)
            shared_memory.write(
                struct.pack("<Q", sequence)
            )

            shared_memory.flush()

            print(
                "sequence={}, delta={:.6f}, theta={:.6f}".format(
                    sequence,
                    delta,
                    theta_command
                )
            )

            next_sample_time += SAMPLE_PERIOD
            remaining_time = (
                next_sample_time - time.perf_counter()
            )

            if remaining_time > 0:
                time.sleep(remaining_time)
            else:
                next_sample_time = time.perf_counter()

    except KeyboardInterrupt:
        print("Transmission stopped.")

    finally:
        shared_memory.close()

print("Python transmission finished.")
