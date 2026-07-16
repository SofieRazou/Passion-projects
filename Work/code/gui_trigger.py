import sys
import time
import subprocess 
import threading
import matlab.engine

pid_1 = "udp.py"
pid_2 = "spring_sim.py"
pid_3 = "C:\Users\javot\Documents\MATLAB\Bern\simulink\sofia_udp_test.m"

eng = matlab.engine.start_matlab()
eng.sofia_udp_test(nargout=0)

process1 = subprocess.Popen([sys.executable, pid_1])
time.sleep(2)
process2 = subprocess.Popen([sys.executable, pid_2])


try:
    process2.wait()
finally:
    process1.terminate()
    process1.wait()
    eng.quit()


print("GUI execution terminated...")
