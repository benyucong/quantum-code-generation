import dimod
import networkx as nx

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


class KClique(QuadradicUnconstrainedBinaryOptimization):
    def __init__(self, graph, k, clique_result, coclique=False):
        self.graph = graph
        self.clique_result = clique_result
        if coclique:
            self.graph = nx.complement(graph)
        self.k = k
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.variables = list(self.graph.nodes)

        # Ensure A > K*B
        self.B = 1
        self.A = self.k * self.B + 1

        ## Aim to select k nodes
        Ha = dimod.generators.combinations(self.variables, self.k, strength=1.0)
        Ha.scale(self.A)
        self.qubo.update(Ha)

        ## Aim to select n(n - 1)/2 edges, i.e., all edges between the k nodes
        n_edges = self.B * (self.k * (self.k - 1) / 2)
        edge_variable_pairs = [(edge[0], edge[1], -1.0) for edge in self.graph.edges]
        Hb = dimod.BinaryQuadraticModel(dimod.BINARY)
        Hb.add_interactions_from(edge_variable_pairs)
        Hb.scale(self.B)
        Hb.offset = n_edges

        # Final Hamiltonian
        self.qubo.update(Hb)

    def get_binary_polynomial(self):
        return self.qubo

    def verify_bitstring(self, string, qubits_to_variables):
        clique = []
        variables_to_qubits = {v: k for k, v in qubits_to_variables.items()}
        for i in range(len(string)):
            if string[variables_to_qubits[self.variables[i]]] == "1":
                clique.append(self.variables[i])

        # Check if the clique is valid
        for i in range(len(clique)):
            for j in range(i + 1, len(clique)):
                if not self.graph.has_edge(clique[i], clique[j]):
                    return False

        # Check if the size of the clique is k
        if len(clique) != self.k:
            return False

        # Check if the clique is equal to the given clique result
        if sorted(clique) != sorted(self.clique_result):
            return False

        return True
