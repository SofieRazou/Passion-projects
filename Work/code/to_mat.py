# -*- coding: utf-8 -*-

import math
import mmap
import os
import struct
import time

FILE_PATH = r"C:\Users\javot\Desktop\sofia_code\shared_data.bin"
FILE_SIZE = 24

if not os.path.isfile(FILE_PATH):
    with open(FILE_PATH, "wb") as file:
        file.write(b"\x00" * FILE_SIZE)

with open(FILE_PATH, "r+b") as file:
    shared_memory = mmap.mmap(
        file.fileno(),
        FILE_SIZE,
        access=mmap.ACCESS_WRITE
    )

    sequence = 0

    try:
        while True:
            current_time = time.perf_counter()

            x_value = math.sin(current_time)
            y_value = math.cos(current_time)

            sequence += 1
            shared_memory.seek(0)
            shared_memory.write(struct.pack("<Q", sequence))

            shared_memory.seek(8)
            shared_memory.write(
                struct.pack("<dd", x_value, y_value)
            )

            sequence += 1
            shared_memory.seek(0)
            shared_memory.write(struct.pack("<Q", sequence))

            shared_memory.flush()

            print(
                "x = {:.4f}, y = {:.4f}".format(
                    x_value,
                    y_value
                )
            )

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Transmission stopped.")

    finally:
        shared_memory.close()
