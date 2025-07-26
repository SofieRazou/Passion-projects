from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import QuantumKernel
from qiskit_machine_learning.algorithms import QSVC
from qiskit.utils import algorithm_globals
from qiskit.primitives import Sampler


class QClassifier:
    def __init__(self, nqubits=4):
        algorithm_globals.random_seed = 42
        self.feature_map = ZZFeatureMap(feature_dimension=nqubits, reps=2, entanglement="linear")
        self.quantum_kernel = QuantumKernel(feature_map=self.feature_map, sampler=Sampler())
        self.model = QSVC(quantum_kernel=self.quantum_kernel)

    def fit(self, X_train, y_train):
        print("Fitting quantum SVM...")
        self.model.fit(X_train, y_train)

    def evaluate(self, X_test, y_test):
        acc = self.model.score(X_test, y_test)
        print(f"Quantum SVM Accuracy: {acc:.3f}\n")
