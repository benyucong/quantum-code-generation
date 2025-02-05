"""
This module contains the Ansatz class, which is used to generate the quantum circuit ansatz for the VQE algorithm.

The current Ansatz configurations are inspired by the following paper:
arXiv:1905.10876v1
"""

import pennylane as qml


class AnsatzCircuit6:
    def __init__(self, num_qubits: int, layers: int):
        self.num_qubits = num_qubits
        self.layers = layers

    def parameter_shapes(self) -> int:
        return self.layers * (
            self.num_qubits * 2 * 2 + self.num_qubits * (self.num_qubits - 1)
        )

    def get_circuit_function(self):
        def circuit(params):
            # Iterator to keep track of which parameter we are at
            param_idx = 0

            for _ in range(self.layers):
                # Apply a layer of Rx and Ry gates
                for qubit in range(self.num_qubits):
                    qml.RX(params[param_idx], wires=qubit)
                    param_idx += 1
                    qml.RY(params[param_idx], wires=qubit)
                    param_idx += 1

                # Apply a layer of CRX gates connecting alternating qubits
                for t_qubit in range(self.num_qubits, 0, -1):
                    for c_qubit in range(self.num_qubits, 0, -1):
                        if t_qubit != c_qubit:
                            qml.CRX(params[param_idx], wires=[t_qubit - 1, c_qubit - 1])
                            param_idx += 1

                # Apply the second layer of Rx and Ry gates
                for qubit in range(self.num_qubits):
                    qml.RX(params[param_idx], wires=qubit)
                    param_idx += 1
                    qml.RY(params[param_idx], wires=qubit)
                    param_idx += 1

        return circuit


class Ansatz:
    def __init__(self, n_qubits: int, layers: int):
        self.n_qubits = n_qubits
        self.layers = layers
        self.ansatz = AnsatzCircuit6(n_qubits, layers)

    def get_circuit(self):
        return self.ansatz.get_circuit_function()

    def get_parameter_shapes(self):
        return self.ansatz.parameter_shapes()
