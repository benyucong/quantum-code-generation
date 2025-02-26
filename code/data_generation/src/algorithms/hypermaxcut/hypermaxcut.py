import itertools
import dimod
import numpy as np

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


class HyperMaxCut(QuadradicUnconstrainedBinaryOptimization):
    def __init__(self, hypergraph, p=1, description="HyperMaxCut"):
        """
        Constructs a BinaryQuadraticModel for the hypermaxcut problem.
        """
        super().__init__(description=description)

        self.hypergraph = hypergraph
        self.n_qubits = hypergraph.n_nodes
        self.p = p

        self.init_params = 0.01 * np.random.rand(2, p)
        self.bqm = self._construct_bqm()

    def _construct_bqm(self):
        """
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
            edge = tuple(edge)
            n = len(edge)
            if n < 2:
                continue
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

                for i in edge:
                    bqm.add_linear(i, -1.0 / n)

                bqm.offset += 1
        return bqm

    def get_binary_polynomial(self):
        return self.bqm
