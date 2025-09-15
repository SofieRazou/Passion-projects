from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

def oracle(circuit, register, marked_state):
    n = len(marked_state)
    for i in range(n):
        if marked_state[i] == '0':
            circuit.x(register[i])
    circuit.h(register[-1])
    circuit.cx(register[0], register[1])
    circuit.h(register[-1])
    for i in range(n):
        if marked_state[i] == '0':
            circuit.x(register[i])

def diffusion(circuit, register):
    circuit.h(register)
    circuit.x(register)
    circuit.h(register[-1])
    circuit.cx(register[0], register[1])
    circuit.h(register[-1])
    circuit.x(register)
    circuit.h(register)

def grover(marked_state):
    n = len(marked_state)
    qr = QuantumRegister(n)
    cr = ClassicalRegister(n)
    qc = QuantumCircuit(qr, cr)

    qc.h(qr)
    num_iter = int(round((2**n)**0.5))
    for _ in range(num_iter):
        oracle(qc, qr, marked_state)
        diffusion(qc, qr)

    qc.measure(qr, cr)

    # Use AerSimulator.run() instead of execute
    simulator = AerSimulator()
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    return list(counts.keys())[0]

# --- Run multiple trials ---
times = 1000
correct = 0
marked_state = input("Enter a 2-qubit state to mark (e.g., '10'): \n")

for _ in range(times):
    result = grover(marked_state)
    if marked_state == result:
        correct += 1

suc_rate = (correct / times) * 100
print(f"Grover's algorithm succeeded {suc_rate}% of the time for marked state {marked_state}.")
