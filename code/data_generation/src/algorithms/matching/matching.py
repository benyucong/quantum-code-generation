import dimod
import networkx as nx
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


class Matching(QuadradicUnconstrainedBinaryOptimization):
    """
    Simple formulation in https://arxiv.org/pdf/1910.05129.pdf
    """

    def __init__(self, graph, matching):
        self.graph = graph
        self.edges = set(tuple(sorted([edge[0], edge[1]])) for edge in graph.edges())
        self.nodes = set(graph.nodes())
        self.matching = matching
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.build_qubo()

    def build_qubo(self):
        B = 1
        A = len(self.graph.nodes) * B + 1

        for node in self.graph.nodes:
            adjacent_edges = self.graph.edges(node)
            adjacent_edges = set(
                tuple(sorted([edge[0], edge[1]])) for edge in adjacent_edges
            )
            # Select one edge from the adjacent edges
            if len(adjacent_edges) > 0:
                bqm = dimod.generators.combinations(adjacent_edges, 1, strength=1.0)
                self.qubo.update(bqm)
        self.qubo.scale(A)

        Hb = dimod.BinaryQuadraticModel(dimod.BINARY)
        for edge in self.edges:
            if "weight" in self.graph.edges[edge]:
                Hb.add_variable(edge, self.graph.edges[edge]["weight"])
            else:
                Hb.add_variable(edge, 1)
        Hb.scale(B)
        self.qubo.update(Hb)

    def get_binary_polynomial(self):
        return self.qubo

    def get_solution(self):
        solution = {}
        for v in self.qubo.variables:
            if v in self.matching:
                solution[v] = 0
            else:
                solution[v] = 1
        return solution

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {"graph": graph_json, "matching": self.matching}

    def get_hash(self):
        match_hash = weisfeiler_lehman_graph_hash(nx.Graph(self.matching))
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{match_hash}"

    def verify_bitstring(self, bitstring, qubits_to_variables):
        variables_to_qubits = {v: k for k, v in qubits_to_variables.items()}
        matching = []

        for edge in self.graph.edges():
            if bitstring[variables_to_qubits[edge]] == "1":
                matching.append(edge)
        print("Matching:")
        print(matching)
        print("Original Matching:")
        print(self.matching)
        for edge in self.matching:
            if edge not in matching:
                return False
        return True
