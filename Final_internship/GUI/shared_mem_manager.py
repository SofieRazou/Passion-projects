import sys
import time 
import numpy as np
from multiprocessing import shared_memory

BUFFER_SIZE = 16
# sine_array=np.sin(np.linspace(0, 2 * np.pi, BUFFER_SIZE)).astype(np.float32)
class SManager:

    def __init__ (self):
        self.sm = None
        self.data = None

    def create_mem (self, mem_name="shared_mem", size=BUFFER_SIZE):
        nbytes = BUFFER_SIZE * np.dtype(np.float32).itemsize

        self.sm = shared_memory.SharedMemory(name=mem_name, create=True, size=nbytes)
        self.data = np.ndarray((BUFFER_SIZE,), dtype=np.float32, buffer=self.sm.buf)

        self.data[:] = 0.0

        return self.sm, self.data

    def deallocate(self):
        self.sm.unlink()

    def write(self, data):
        new_data = np.array(data, dtype=np.float32)
        self.data[:len(new_data)] = new_data

    def close(self):
        self.sm.close()

#-------TEST MAIN ---------- #

# def main():
#     manager = SManager()
#     sm, data = manager.create_mem(mem_name="shared_mem", size=BUFFER_SIZE)
#     print("Shared memory created. Press Ctrl+C to exit.")

#     start_time = time.time()
#     try:
#         while True:
#             sine_array = np.sin(np.linspace(0, 2 * np.pi, BUFFER_SIZE) + (time.time() - start_time)).astype(np.float32)
#             manager.write(sine_array)
#             time.sleep(0.01)
#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         print("Data registred in shared memory")
#     # finally:
#     #     manager.close()
#     #     manager.deallocate()
#     #     print("Shared memory deallocated.") 

# if __name__ == "__main__":
#     main()
