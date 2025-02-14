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

    def get_params(self) -> int:
        return self.layers * (
            self.num_qubits * 2 * 2 + self.num_qubits * (self.num_qubits - 1)
        )

    def get_circuit_function(self):
        def circuit(single_qubit_params, two_qubit_params):
            # Iterator to keep track of which parameter we are at
            for l in range(self.layers):
                # Apply a layer of Rx and Ry gates
                for qubit in range(self.num_qubits):
                    qml.RX(single_qubit_params[l][qubit][0], wires=qubit)
                    qml.RY(single_qubit_params[l][qubit][1], wires=qubit)

                # Apply a layer of CRX gates connecting alternating qubits
                for t_qubit in range(self.num_qubits - 1, 0, -1):
                    for c_qubit in range(self.num_qubits - 1, 0, -1):
                        if t_qubit != c_qubit:
                            qml.CRX(
                                two_qubit_params[l][t_qubit][0],
                                wires=[t_qubit - 1, c_qubit - 1],
                            )

                # Apply the second layer of Rx and Ry gates
                for qubit in range(self.num_qubits):
                    qml.RX(single_qubit_params[l][qubit][2], wires=qubit)
                    qml.RY(single_qubit_params[l][qubit][3], wires=qubit)

        return circuit

    def get_parameter_shapes(self):
        return (self.layers, self.num_qubits, 4), (self.layers, self.num_qubits, 1)


class Ansatz:
    """
    A class to represent an Ansatz for quantum circuits.

    Attributes:
    -----------
    n_qubits : int
        The number of qubits in the quantum circuit.
    layers : int
        The number of layers in the quantum circuit.
    depth : int
        The depth of the quantum circuit.
    ansatz : AnsatzCircuit6
        An instance of AnsatzCircuit6 representing the quantum circuit.

    Methods:
    --------
    get_circuit_function():
        Returns the circuit function of the ansatz.

    get_parameter_shapes():
        Returns the parameter shapes of the ansatz.
    """

    def __init__(self, n_qubits: int, layers: int):
        self.n_qubits = n_qubits
        self.layers = layers
        self.ansatz = AnsatzCircuit6(n_qubits, layers)

    def get_circuit_function(self):
        """
        Retrieve the circuit function from the ansatz.

        Returns:
            function: The circuit function defined in the ansatz.
        """
        return self.ansatz.get_circuit_function()

    def get_parameter_shapes(self):
        """
        Retrieve the shapes of the parameters used in the ansatz.

        Returns:
            list: A list of shapes for each parameter in the ansatz.
        """
        return self.ansatz.get_parameter_shapes()
