import pennylane as qml

class Sim13:

    def __init__(self, num_qubits, n_layers):
        self.num_qubits = num_qubits
        self.n_layers = n_layers
        self.ansatz_id = 13

    def get_circuit(self):

        def circuit(single_qubit_params, two_qubit_params):
            for d in range(self.n_layers):
                for i in range(self.num_qubits):
                    qml.RY(single_qubit_params[d][i][0], wires=i)

                qml.CRZ(two_qubit_params[d][0][0], wires=[self.num_qubits - 1, 0])
                
                for i in reversed(range(self.num_qubits - 1)):
                    qml.CRZ(two_qubit_params[d][i + 1][0], wires=[i, i + 1])
                
                for i in range(self.num_qubits):
                    qml.RY(single_qubit_params[d][i][1], wires=i)
                
                qml.CRZ(two_qubit_params[d][0][1], wires=[self.num_qubits - 1, self.num_qubits - 2])
                qml.CRZ(two_qubit_params[d][1][1], wires=[0, self.num_qubits - 1])
                
                for i in range(self.num_qubits - 2):
                    qml.CRZ(two_qubit_params[d][i + 2][1], wires=[i, i + 1])

        return circuit

    def get_params_shape(self):
        return (self.n_layers, self.num_qubits, 2), (self.n_layers, self.num_qubits, 2)