import dimod
import networkx as nx

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


class KClique(QuadradicUnconstrainedBinaryOptimization):
    def __init__(self, graph, k, coclique=False, description="KClique"):
        super().__init__(description=description)

        self.graph = graph
        if coclique:
            self.graph = nx.complement(graph)
        self.k = k
        self.qubo = dimod.BinaryQuadraticModel.empty(dimod.BINARY)

        ## Aim to select k nodes
        bqm = dimod.generators.combinations(self.graph.nodes, self.k, strength=1.0)
        self.qubo.update(bqm)

        ## Aim to select n(n - 1)/2 edges, i.e., all edges between the k nodes
        n_edges = self.k * (self.k - 1) / 2
        # print("Number of selected edges: ", n_edges)
        bqm = dimod.generators.combinations(self.graph.edges, n_edges, strength=1.0)
        self.qubo.update(bqm)

        # For each selected edge, we must select the source and target nodes
        poly = {}
        for edge in self.graph.edges:
            poly[edge] = 1
            poly[(edge, edge[0], edge[1])] = -2
            poly[(edge[0], edge[1])] = 1

        for v in self.qubo.linear:
            poly[(v,)] = self.qubo.get_linear(v)
        for v in self.qubo.quadratic:
            poly[(v[0], v[1])] = self.qubo.get_quadratic(*v)

        self.poly = dimod.BinaryPolynomial(poly, dimod.BINARY)

        bqm = dimod.make_quadratic(self.poly, 3.0, dimod.BINARY)
        self.qubo.update(bqm)
        self.qubo.offset += n_edges

    def get_binary_polynomial(self):
        return self.poly
