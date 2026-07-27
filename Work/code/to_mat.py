import math
import os
import struct
import time

FILE_PATH = r"C:\Users\javot\Desktop\sofia_code\shared_data.bin"

FILE_SIZE = 24
SAMPLE_PERIOD = 0.01   # 100 Hz (10ms step)
DURATION = 20.0        # seconds

folder = os.path.dirname(FILE_PATH)

if not os.path.isdir(folder):
    raise FileNotFoundError(
        "Folder does not exist: {}".format(folder)
    )

# Create the file only when it does not exist or has the wrong size
if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) != FILE_SIZE:
    with open(FILE_PATH, "wb") as file:
        file.write(b"\x00" * FILE_SIZE)
        file.flush()
        os.fsync(file.fileno())

sequence = 0
start_time = time.perf_counter()
next_sample_time = start_time

theta_command = 0.0  # Accumulated vehicle heading angle [rad]

print("Starting Python writer...")
print("Writing to:", FILE_PATH)

try:
    with open(FILE_PATH, "r+b", buffering=0) as file:

        while time.perf_counter() - start_time < DURATION:
            elapsed_time = time.perf_counter() - start_time

            # 1. Gentle, noticeable steering angle delta [radians] (~11.5 degrees max)
            delta = 0.2 * math.sin(0.4 * elapsed_time)

            # 2. Update heading angle (theta) over time based on current steering angle
            # Slow speed turning rate factor
            theta_command += delta * SAMPLE_PERIOD * 1.5

            # Odd sequence: writing has started
            sequence += 1

            file.seek(0)
            file.write(
                struct.pack("<Q", sequence)
            )

            # Write the two double values (steering delta & cumulative heading)
            file.seek(8)
            file.write(
                struct.pack(
                    "<dd",
                    float(delta),
                    float(theta_command)
                )
            )

            # Even sequence: writing has finished
            sequence += 1

            file.seek(0)
            file.write(
                struct.pack("<Q", sequence)
            )

            file.flush()

            print(
                "sequence={}, delta={:.6f}, theta={:.6f}".format(
                    sequence,
                    delta,
                    theta_command
                )
            )

            next_sample_time += SAMPLE_PERIOD
            remaining_time = next_sample_time - time.perf_counter()

            if remaining_time > 0:
                time.sleep(remaining_time)
            else:
                next_sample_time = time.perf_counter()

except KeyboardInterrupt:
    print("Transmission stopped by user.")

print("Python transmission finished.")
