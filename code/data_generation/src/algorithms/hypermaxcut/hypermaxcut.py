import itertools
import pennylane as qml
from pennylane import numpy as np
np.random.seed(0)


class HyperMaxCut:

    def __init__(self, hypergraph, p = 1):
        self.hypergraph = hypergraph
        self.n_qubits = hypergraph.n_nodes
        self.coeffs = []
        self.observables = []
        self._construct_full_hamiltonian()
        self.p = p
        self.init_params = 0.01*np.random.rand(2, p, requires_grad=True)

    
    def _construct_full_hamiltonian(self):
        # Construct the cost Hamiltonian for the hypergraph
        for edge in self.hypergraph.hyperedges:
            coeffs, observables = self._sum_term_in_cost_hamiltonian(edge)
            self.coeffs.extend(coeffs)
            self.observables.extend(observables)


    def _sum_term_in_cost_hamiltonian(self, edge):
        n_nodes = len(edge)
        assert n_nodes > 1, "An edge must have at least 2 nodes"
        coeffs = [2**(n_nodes-2) - 1]
        observables = [qml.prod(*[qml.Identity(i) for i in edge])]

        for subset_size in range(2, n_nodes + 1):
            if subset_size % 2 == 0:
                for subset in itertools.combinations(edge, subset_size):
                    coeffs.append(2**(n_nodes-2))
                    observables.append(qml.prod(*[qml.PauliZ(i) for i in subset]))

        return coeffs, observables
    
    def get_cost_hamiltonian(self):
        return qml.ops.op_math.LinearCombination(self.coeffs, self.observables)