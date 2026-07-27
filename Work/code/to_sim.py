Cannot propagate bus signal from 'Output Port 1' of 'driving_scene1/Scenario Reader' to 'Input Port 1' of 'driving_scene1/Demux' because this input port requires a non-bus signal.

If the destination block is a bus-capable block, ensure that the block configuration and its input signal(s) meet the requirements for bus support. Please see Simulink documentation for further information on composite (i.e. bus) signals and their proper usage. Alternately, if the input bus signal is virtual; consists only of scalar elements, 1-D elements, or either row or column vectors; and all elements have the same data type, signal type, and sampling mode, consider inserting a Bus to Vector conversion block in the signal path. Otherwise, consider using a Bus Selector block in the signal path.




import numpy as np
import socket

UDP_IP = "192.168.0.10"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

trajectory = np.array([
    [1.0, 2.0],
    [3.0, 4.0],
    [5.0, 6.0]
], dtype=np.float32)

packet = trajectory.tobytes()

sock.sendto(packet, (UDP_IP, UDP_PORT))
