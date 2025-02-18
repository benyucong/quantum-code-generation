"""
This module contains the Ansatz class, which is used to generate the quantum circuit ansatz for the VQE algorithm.

The current Ansatz configurations are inspired by the following paper:
arXiv:1905.10876v1
"""

import pennylane as qml
from abc import ABC, abstractmethod


class Ansatz(ABC):
    """
    Base abstract class for quantum circuit ansatz.
    """

    def __init__(self, n_qubits: int, layers: int):
        self.n_qubits = n_qubits
        self.layers = layers

    @abstractmethod
    def get_circuit(self):
        """
        Returns the circuit function for the ansatz.
        """
        pass

    @abstractmethod
    def get_parameter_shapes(self):
        """
        Returns the parameter shapes for the ansatz.
        """
        pass


class AnsatzCircuit6(Ansatz):
    def __init__(self, num_qubits: int, layers: int):
        super().__init__(num_qubits, layers)

    def get_circuit(self):
        def circuit(single_qubit_params, two_qubit_params):
            # Iterate over layers.
            for l in range(self.layers):
                # Apply a layer of RX and RY gates.
                for qubit in range(self.n_qubits):
                    qml.RX(single_qubit_params[l][qubit][0], wires=qubit)
                    qml.RY(single_qubit_params[l][qubit][1], wires=qubit)

                # Apply a layer of CRX gates connecting alternating qubits.
                for t_qubit in range(self.n_qubits - 1, 0, -1):
                    for c_qubit in range(self.n_qubits - 1, 0, -1):
                        if t_qubit != c_qubit:
                            qml.CRX(
                                two_qubit_params[l][t_qubit][0],
                                wires=[t_qubit - 1, c_qubit - 1],
                            )

                # Apply the second layer of RX and RY gates.
                for qubit in range(self.n_qubits):
                    qml.RX(single_qubit_params[l][qubit][2], wires=qubit)
                    qml.RY(single_qubit_params[l][qubit][3], wires=qubit)

        return circuit

    def get_parameter_shapes(self):
        return (self.layers, self.n_qubits, 4), (self.layers, self.n_qubits, 1)


class AnsatzCircuit13(Ansatz):
    def __init__(self, num_qubits, layers):
        super().__init__(num_qubits, layers)

    def get_circuit(self):
        def circuit(single_qubit_params, two_qubit_params):
            for d in range(self.layers):
                for i in range(self.n_qubits):
                    qml.RY(single_qubit_params[d][i][0], wires=i)

                qml.CRZ(two_qubit_params[d][0][0], wires=[self.n_qubits - 1, 0])

                for i in reversed(range(self.n_qubits - 1)):
                    qml.CRZ(two_qubit_params[d][i + 1][0], wires=[i, i + 1])

                for i in range(self.n_qubits):
                    qml.RY(single_qubit_params[d][i][1], wires=i)

                qml.CRZ(
                    two_qubit_params[d][0][1],
                    wires=[self.n_qubits - 1, self.n_qubits - 2],
                )
                qml.CRZ(two_qubit_params[d][1][1], wires=[0, self.n_qubits - 1])

                for i in range(self.n_qubits - 2):
                    qml.CRZ(two_qubit_params[d][i + 2][1], wires=[i, i + 1])

        return circuit

    def get_parameter_shapes(self):
        return (self.layers, self.n_qubits, 2), (self.layers, self.n_qubits, 2)


class AnsatzCircuit5(Ansatz):
    def __init__(self, num_qubits, layers):
        super().__init__(num_qubits, layers)

    def get_circuit(self):
        def circuit(single_qubit_params, two_qubit_params):
            for d in range(self.layers):
                for i in range(self.n_qubits):
                    qml.RX(single_qubit_params[d][i][0], wires=i)
                    qml.RZ(single_qubit_params[d][i][1], wires=i)

                for control_qubit in reversed(range(self.n_qubits)):
                    for target_qubit in reversed(range(self.n_qubits)):
                        if control_qubit != target_qubit:
                            qml.CRZ(
                                two_qubit_params[d][target_qubit][0],
                                wires=[control_qubit, target_qubit],
                            )

                for i in range(self.n_qubits):
                    qml.RX(single_qubit_params[d][i][2], wires=i)
                    qml.RZ(single_qubit_params[d][i][3], wires=i)

        return circuit

    def get_parameter_shapes(self):
        return (self.layers, self.n_qubits, 4), (self.layers, self.n_qubits, 1)


def get_ansatz(ansatz_type: int, num_qubits: int, layers: int) -> Ansatz:
    """
    Returns an ansatz instance based on the provided ansatz type.

    Parameters:
        ansatz_type (int): The type of ansatz to generate. Options: [5, 6, 13].
        num_qubits (int): The number of qubits.
        layers (int): The number of layers (or depth) of the ansatz.

    Returns:
        Ansatz: An instance of an ansatz subclass.
    """
    if ansatz_type == 6:
        return AnsatzCircuit6(num_qubits, layers)
    elif ansatz_type == 13:
        return AnsatzCircuit13(num_qubits, layers)
    elif ansatz_type == 5:
        return AnsatzCircuit5(num_qubits, layers)
    else:
        raise ValueError(f"Unknown ansatz type: {ansatz_type}")
