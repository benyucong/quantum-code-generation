from data_generation.vqe_solver import VQESolver
from data_generation.hypermaxcut.hypergraph import HyperGraph


class HyperMaxCutSolver(VQESolver):
    def __init__(self, n_qubits: int, n_layers: int, hypergraph: HyperGraph):
        super().__init__(n_qubits=n_qubits, layers=n_layers)
        self.hypergraph = hypergraph

        # Construct the Hamiltonian
        self.coeffifiencts, self.pauli_strings = self.construct_hamiltonian()

    def construct_hamiltonian(self):
        return 1, 2

    def solve_classically(self):
        pass

    def solve_vqe(self):
        return self.coeffifiencts, self.pauli_strings

    def get_qasm_circuit(self):
        pass
