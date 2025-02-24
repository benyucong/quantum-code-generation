import pennylane as qml
from pennylane import numpy as np

class Sim6:

    def __init__(self, num_qubits, n_layers):
        self.num_qubits = num_qubits
        self.n_layers = n_layers
        self.ansatz_id = 6

    def get_circuit(self):

        def circuit(single_qubit_params, two_qubit_params):
            for d in range(self.n_layers):
                for i in range(self.num_qubits):
                    qml.RX(single_qubit_params[d][i][0], wires=i)
                    qml.RZ(single_qubit_params[d][i][1], wires=i)
                
                for control_qubit in reversed(range(self.num_qubits)):
                    for target_qubit in reversed(range(self.num_qubits)):
                        if control_qubit != target_qubit:
                            qml.CRX(two_qubit_params[d][target_qubit][0], 
                                    wires=[control_qubit, target_qubit])
                
                for i in range(self.num_qubits):
                    qml.RX(single_qubit_params[d][i][2], wires=i)
                    qml.RZ(single_qubit_params[d][i][3], wires=i)

        return circuit

    def get_params_shape(self):
        return (self.n_layers, self.num_qubits, 4), (self.n_layers, self.num_qubits, 1)