class VQESolver:
    def __init__(self, n_qubits: int, layers: int):
        self.n_qubits = n_qubits
        self.layers = layers

    def construct_hamiltonian(self):
        pass

    def solve_classically(self):
        pass

    def solve_vqe(self):
        pass

    def get_qasm_circuit(self):
        pass

    def get_qubits(self):
        return self.n_qubits

    def get_layers(self):
        return self.layers
