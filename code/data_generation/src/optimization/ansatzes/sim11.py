import pennylane as qml
from pennylane import numpy as np

class Sim11:

    def __init__(self, num_qubits, n_layers):
        self.num_qubits = num_qubits
        self.n_layers = n_layers
        self.ansatz_id = 11

    def get_circuit(self):

        def circuit(single_qubit_params):
            for d in range(self.n_layers):
                for i in range(self.num_qubits):
                    qml.RY(single_qubit_params[d][i][0], wires=i)
                    qml.RZ(single_qubit_params[d][i][1], wires=i)
                
                for i in range(0, self.num_qubits - 1, 2):
                    qml.CNOT(wires=[i + 1, i])
                
                for i in range(1, self.num_qubits - 1, 2):
                    qml.RY(single_qubit_params[d][i][2], wires=i)
                    qml.RZ(single_qubit_params[d][i][3], wires=i)
                    if i != self.num_qubits - 2:
                        qml.RY(single_qubit_params[d][i + 1][2], wires=i + 1)
                        qml.RZ(single_qubit_params[d][i + 1][3], wires=i + 1)
                    qml.CNOT(wires=[i + 1, i])

        return circuit

    def get_params_shape(self):
        return (self.n_layers, self.num_qubits, 4), None