from multiprocessing import shared_memory
import numpy as np
import time

# Create shared memory (8 bytes for one float64)
shm = shared_memory.SharedMemory(
    name="yaw_memory",
    create=True,
    size=8
)

# Create numpy view
yaw_shared = np.ndarray(
    (1,),
    dtype=np.float64,
    buffer=shm.buf
)

# Initial value
yaw_shared[0] = 0.0

print("Shared memory created")

try:
    while True:
        # Replace this with your yaw measurement
        yaw = 45.0

        # Write yaw
        yaw_shared[0] = yaw

        print("Yaw sent:", yaw)

        time.sleep(0.01)   # 100 Hz

except KeyboardInterrupt:
    pass

finally:
    shm.close()
    shm.unlink()
