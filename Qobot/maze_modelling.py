from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import Aer
import numpy as np
import matplotlib.pyplot as plt

import serial
import time

#------ Establishing serial communication with arduino ----------
arduino = serial.Serial('/dev/cu.usbmodem11301', 9600, timeout=1) 
time.sleep(2)  # pending for connection

def send_to_arduino(dx, dy):
    if dx == 0 and dy == -1:
        arduino.write(b'N')  # North
    elif dx == 0 and dy == 1:
        arduino.write(b'S')  # South
    elif dx == -1 and dy == 0:
        arduino.write(b'W')  # West
    elif dx == 1 and dy == 0:
        arduino.write(b'E')  # East
    time.sleep(1.5)  # wait for movement to finish

# --- Robot Class ---
class QRobot:
    def __init__(self, x, y, maze, goal):
        self.x = x
        self.y = y
        self.maze = maze
        self.goal = goal
        self.path = []
        self.history = [(x, y)]

    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < len(self.maze) and 0 <= new_y < len(self.maze[0]):
            if self.maze[new_x][new_y] == 0:
                self.x, self.y = new_x, new_y
                self.path.append((dx, dy))
                self.history.append((self.x, self.y))
                return True
        return False

    def dtg(self):
        gx, gy = self.goal
        return abs(self.x - gx) + abs(self.y - gy)

    def fitness(self):
        return 1 / (1 + self.dtg())

# --- Maze Setup (new solvable maze) ---
maze = [
    [0, 0, 1, 1],
    [1, 0, 1, 0],
    [1, 0, 0, 0],
    [1, 1, 1, 0]
]

start = (0, 0)
goal = (3, 3)
robot = QRobot(start[0], start[1], maze, goal)

# --- Quantum Registers ---
qreg = QuantumRegister(2, 'q')  # 2 qubits for directions
creg = ClassicalRegister(2, 'c')
qc = QuantumCircuit(qreg, creg)

# --- Prepare superposition of all directions ---
qc.h(qreg[0])
qc.h(qreg[1])
qc.barrier()

# --- Quantum Measurement & Direction Mapping ---
def measure_direction(qc, qreg, creg):
    meas_qc = qc.copy()
    meas_qc.measure(qreg, creg)
    
    backend = Aer.get_backend('aer_simulator')
    compiled = transpile(meas_qc, backend)
    result = backend.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured_state = list(counts.keys())[0]

    if measured_state == '00':
        return (0, -1)  # North
    elif measured_state == '01':
        return (0, 1)   # South
    elif measured_state == '10':
        return (-1, 0)  # West
    elif measured_state == '11':
        return (1, 0)   # East
    else:
        return (0, 0)

# --- Main Test Loop ---
def main():
    steps = 20
    for _ in range(steps):
        dx, dy = measure_direction(qc, qreg, creg)
        send_to_arduino(dx,dy)
        moved = robot.move(dx, dy)
        
        print(f"Robot at {robot.x, robot.y}, moved {dx, dy}, success={moved}")

        if (robot.x, robot.y) == goal:
            print("Goal reached!")
            break

    print("Robot path:", robot.history)

    plt.imshow(maze, cmap='Greys')
    path_x, path_y = zip(*robot.history)
    plt.plot(path_y, path_x, marker='o', color='red')
    plt.scatter(goal[1], goal[0], marker='*', color='gold', s=200)
    plt.title("Robot Path in Maze")
    plt.show()


if __name__ == "__main__":
    main()
