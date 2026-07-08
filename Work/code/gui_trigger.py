import sys
import time
import subprocess 
import threading
pid_2 = "gui_arch.py"
pid_1 = "udp.py"

process1 = subprocess.Popen([sys.executable, pid_1])
time.sleep(2)
process2 = subprocess.Popen([sys.executable, pid_2])

try:
    process2.wait()
finally:
    process1.terminate()
    process1.wait()


print("GUI execution terminated...")
