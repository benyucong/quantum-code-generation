# import itertools
# import pennylane as qml
# from pennylane import numpy as np


# class HyperMaxCut:

#     def __init__(self, hypergraph, p = 1):
#         self.hypergraph = hypergraph
#         self.n_qubits = hypergraph.n_nodes
#         self.coeffs = []
#         self.observables = []
#         self._construct_full_hamiltonian()
#         self.p = p
#         self.init_params = 0.01*np.random.rand(2, p, requires_grad=True)


#     def _construct_full_hamiltonian(self):
#         # Construct the cost Hamiltonian for the hypergraph
#         for edge in self.hypergraph.hyperedges:
#             coeffs, observables = self._sum_term_in_cost_hamiltonian(edge)
#             self.coeffs.extend(coeffs)
#             self.observables.extend(observables)


#     def _sum_term_in_cost_hamiltonian(self, edge):
#         n_nodes = len(edge)
#         assert n_nodes > 1, "An edge must have at least 2 nodes"
#         coeffs = [2**(n_nodes-2) - 1]
#         observables = [qml.prod(*[qml.Identity(i) for i in edge])]

#         for subset_size in range(2, n_nodes + 1):
#             if subset_size % 2 == 0:
#                 for subset in itertools.combinations(edge, subset_size):
#                     coeffs.append(2**(n_nodes-2))
#                     observables.append(qml.prod(*[qml.PauliZ(i) for i in subset]))

#         return coeffs, observables

#     def get_cost_hamiltonian(self):
#         return qml.ops.op_math.LinearCombination(self.coeffs, self.observables)
import itertools
import dimod
import numpy as np


class HyperMaxCut:
    def __init__(self, hypergraph, p=1):
        """
        Constructs a BinaryQuadraticModel for the hypermaxcut problem.

        Args:
            hypergraph: An object with attributes:
                - n_nodes: Number of nodes (to be used as qubits)
                - hyperedges: An iterable of hyperedges, each given as a list or tuple of node indices.
            p: An optional parameter (e.g. number of layers) kept for compatibility.
        """
        self.hypergraph = hypergraph
        self.n_qubits = hypergraph.n_nodes
        self.p = p
        # For VQE/QAOA parameter initialization, even if not used in the BQM:
        self.init_params = 0.01 * np.random.rand(2, p)
        self.bqm = self._construct_bqm()

    def _construct_bqm(self):
        """
        Construct a BinaryQuadraticModel for hypermaxcut.

        For each hyperedge:
          - If the hyperedge has exactly 2 nodes, use the standard maxcut QUBO term:
              maximize (x_i + x_j - 2 x_i x_j)
            which (as a minimization problem) corresponds to adding linear terms -1 and a quadratic term 2,
            with an appropriate constant offset.
          - For hyperedges with more than 2 nodes, we apply a heuristic reduction: we add pairwise
            quadratic terms between all nodes in the hyperedge (normalized by the number of pairs)
            and a small linear term for each node. This is not an exact reduction, but it gives a quadratic
            model that somewhat reflects the desire to "cut" the hyperedge.
        """
        bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, vartype=dimod.BINARY)

        for edge in self.hypergraph.hyperedges:
            edge = tuple(edge)  # ensure it's hashable (e.g. a tuple)
            n = len(edge)
            if n < 2:
                continue  # ignore degenerate hyperedges
            if n == 2:
                # Standard maxcut term for an edge (i, j):
                # Objective (to maximize): x_i + x_j - 2 x_i x_j.
                # For minimization, add: 2*x_i*x_j - x_i - x_j, with constant offset +1.
                i, j = edge
                bqm.add_linear(i, -1)
                bqm.add_linear(j, -1)
                bqm.add_quadratic(i, j, 2)
                bqm.offset += 1
            else:
                # For a hyperedge with more than 2 nodes, we use a heuristic:
                # Add pairwise quadratic terms with weight normalized by the number of pairs,
                # and add small linear terms to encourage a "cut."
                num_pairs = len(list(itertools.combinations(edge, 2)))
                weight = 2.0 / num_pairs  # heuristic weight
                for i, j in itertools.combinations(edge, 2):
                    bqm.add_quadratic(i, j, weight)
                # Add linear terms (heuristic)
                for i in edge:
                    bqm.add_linear(i, -1.0 / n)
                # Increase offset (heuristic)
                bqm.offset += 1
        return bqm

    def get_binary_polynomial(self):
        """
        Returns the BinaryQuadraticModel (BQM) for the hypermaxcut problem.
        """
        return self.bqm
