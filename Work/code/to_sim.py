
Simulink cannot propagate the variable-size mode from the 'Output Port 1' of 'SimpleScenarioAndSensorModel3DSimulation/UDP Receive' to the 'Input Port 1' of 'SimpleScenarioAndSensorModel3DSimulation/Byte Unpack'. This input port expects a fixed-size mode. Examine the configuration of 'SimpleScenarioAndSensorModel3DSimulation/Byte Unpack' for one of the following scenarios: 1) the block does not support variable-size signals; 2) the block supports variable-size signals but needs to be configured for them.



import numpy as np
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

trajectory = np.array([
    [55.8, 5.9],
    [42.4, 16.4],
    [37.3, 18.3],
    [28.1, 25.6],
    [20.3, 17.9],
    [18.7, -5.3],
    [14.6, 10.6],
    [4.6, 12.8],
    [2.2, 21.3],
    [-1.8, 30.2],
    [-4.8, 17.9],
    [-4.9, 5.5],
    [1.6, -4.4],
    [10.8, -7.1],
    [14.9, -13.1],
    [26.0, -16.8],
    [42.7, -31.8],
    [51.1, -10.1],
    [53.4, -3.3],
    [55.8, 5.9]
],dtype = np.float32)

packet = trajectory.tobytes()

try:
    while True:
        sock.sendto(packet, (UDP_IP, UDP_PORT))

except KeyboardInterrupt:
    print("Trajectory communication stopped by user...")

finally:
    print("Trajectory data deployed in simulink model")
    sock.close()

