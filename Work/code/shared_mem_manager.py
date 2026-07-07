import sys
import numpy as np
from multiprocessing import shared_memory

BUFFER_SIZE = 1024
sine_array = np.sin(np.linspace(0, 2 * np.pi, BUFFER_SIZE)).astype(np.float64)
class SManager:
    def create_mem (self, mem_name="shared_mem", size=1024):
        sm = shared_memory.SharedMemory(create=True, size= BUFFER_SIZE, name = "udp_share")
        b = np.ndarray(sine_array.shape, dtype=sine_array.dtype, buffer=sm.buf)
        b[:] = sine_array[:]
        return sm, b
    def deallocate(self):
        pass
    def write(self, data):
        pass
    def upd(self, data, write_enable):
        pass
