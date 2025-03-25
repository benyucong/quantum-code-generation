import dimod
import networkx as nx

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


def append_dict(d, key, value):
    if key not in d:
        d[key] = value
    else:
        d[key] += value


class GraphIsomorphism(QuadradicUnconstrainedBinaryOptimization):
    def __init__(self, graph1, graph2, automorphism) -> None:
        self.graph1 = graph1
        self.graph2 = graph2
        self.automorphism = automorphism
        assert len(graph1.nodes()) == len(graph2.nodes())
        self.bqm = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.isomorphism_is_bijective()
        self.isomorphism_respects_edges()

    def isomorphism_is_bijective(self):
        # For every node in graph1, there must be exactly one node in graph2
        for node1 in self.graph1.nodes():
            vars = [(node1, node2) for node2 in self.graph2.nodes()]
            constraint = dimod.generators.combinations(vars, 1, strength=1)
            self.bqm.update(constraint)
        # For every node in graph2, there must be exactly one node in graph1
        for node2 in self.graph2.nodes():
            vars = [(node1, node2) for node1 in self.graph1.nodes()]
            constraint = dimod.generators.combinations(vars, 1, strength=1)
            self.bqm.update(constraint)

    def isomorphism_respects_edges(self):
        # If there is no edge (i, j) in graph1, then it must be so that there is no edge (u, v) in graph2
        quadratic = {}
        complete_graph = nx.complete_graph(len(self.graph1.nodes()))
        for i, j in complete_graph.edges():
            if (i, j) not in self.graph1.edges():
                for u, v in self.graph2.edges():
                    append_dict(quadratic, ((i, u), (j, v)), 1)

        # If there is no edge (u, v) in graph2, then it must be so that there is no edge (i, j) in graph1
        complete_graph = nx.complete_graph(len(self.graph2.nodes()))
        for u, v in complete_graph.edges():
            if (u, v) not in self.graph2.edges():
                for i, j in self.graph1.edges():
                    append_dict(quadratic, ((i, u), (j, v)), 1)

        self.bqm.update(dimod.BinaryQuadraticModel({}, quadratic, 0, dimod.BINARY))

    def get_binary_polynomial(self):
        return self.bqm

    def get_problem_data(self):
        return None

    def verify_bitstring(self, bitstring, qubits_to_variables):
        isomorphism = {}
        for i in range(len(bitstring)):
            if bitstring[i] == "1":
                node1 = qubits_to_variables[i][0]
                node2 = qubits_to_variables[i][1]
                isomorphism[node1] = node2

        # Isomorphism is bijective between nodes
        if len(isomorphism) != len(self.graph1.nodes()):
            return False
        if len(set(isomorphism.values())) != len(self.graph2.nodes()):
            return False

        # Isomorphism respects edges
        for i, j in self.graph1.edges():
            if (isomorphism[i], isomorphism[j]) not in self.graph2.edges():
                return False

        for key, value in isomorphism.items():
            if self.automorphism[key] != value:
                return False

        return True
