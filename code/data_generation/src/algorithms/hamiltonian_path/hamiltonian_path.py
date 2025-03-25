import dimod
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


class HamiltonianPath(QuadradicUnconstrainedBinaryOptimization):
    """
    This implementation is based on https://arxiv.org/pdf/1302.5843.pdf
    For a weighted graph this problem is the traveling salesman problem
    """

    def __init__(self, graph, hamiltonian_path, start_node, end_node, cycle=False):
        """
        Types:
            path: both start and end node are provided and they are different,
            cycle: both start and end node are provided and they are the same
            traveling_salesman: cycle with minimal total weight, will be calculated automatically
            if the graph has weights

        """
        self.graph = graph
        self.hamiltonian_path = hamiltonian_path
        self.start_index = 0
        self.end_index = len(graph.nodes)
        self.start_var = None
        self.end_var = None
        self.start_node = start_node
        self.end_node = end_node
        self.cycle = cycle
        if start_node is not None and end_node is not None:
            self.nodes = [n for n in graph.nodes if n not in [start_node, end_node]]
            self.start_var = (start_node, 0)
            self.end_var = (end_node, len(graph.nodes) - 1)
            self.start_index = 1
            self.end_index = len(graph.nodes) - 1
        elif start_node is not None:
            self.nodes = list(graph.nodes) - [start_node]
            self.start_var = (start_node, 0)
            self.start_index = 1

        self.path_interval = range(self.start_index, self.end_index)
        self.qubo = dimod.BinaryQuadraticModel.empty(dimod.BINARY)
        # These correspond to the constraints in paper https://arxiv.org/abs/1302.5843
        self.H_A()
        self.H_B()

    def H_A(self):
        ## Every node must be visited exactly once except the start node in cycle
        for u in self.nodes:
            vars_i = [(u, j) for j in self.path_interval]
            # print(vars_i)
            bqm = dimod.generators.combinations(vars_i, 1, strength=1.0)
            self.qubo.update(bqm)

        ## Every place in the path/cycle must be occupied by exactly one node
        for j in self.path_interval:
            vars_j = [(u, j) for u in self.nodes]
            # print(vars_j)
            bqm = dimod.generators.combinations(vars_j, 1, strength=1.0)
            self.qubo.update(bqm)

        ## If x_(u,i) = 1 and x_(v, i + 1) = 1 then there must be an edge between u and v
        quadratic = {}
        for u in self.nodes:
            for v in self.nodes:
                if u != v and (u, v) not in self.graph.edges:
                    for i in self.path_interval:
                        quadratic[(u, i), (v, i + 1)] = 1
        self.qubo.update(dimod.BinaryQuadraticModel.from_qubo(quadratic))

    def H_B(self):
        # For a weighted graph, the total weight of the path/cycle should be minimal
        if "weight" in self.graph.edges:
            quadratic = {}
            for u in self.graph.nodes:
                for v in self.graph.nodes:
                    if (u, v) in self.graph.edges:
                        for i in self.path_interval:
                            quadratic[(u, i), (v, i + 1)] = self.graph.edges[(u, v)][
                                "weight"
                            ]
                            if i == 1 and self.start_var is not None:
                                quadratic[self.start_var, (v, i)] = self.graph.edges[
                                    (u, v)
                                ]["weight"]
                            if i == self.end_index - 1 and self.end_var is not None:
                                quadratic[(u, i), self.end_var] = self.graph.edges[
                                    (u, v)
                                ]["weight"]
            self.qubo.update(dimod.BinaryQuadraticModel.from_qubo(quadratic))

    def get_solution(self):
        solution = {}
        for var in self.qubo.variables:
            node = var[0]
            i = var[1]
            if i < len(self.hamiltonian_path) and self.hamiltonian_path[i][0] == node:
                solution[var] = 1
            elif (
                i == len(self.hamiltonian_path) and self.hamiltonian_path[-1][1] == node
            ):
                solution[var] = 1
            else:
                solution[var] = 0
        return solution

    def get_binary_polynomial(self):
        return self.qubo

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "hamiltonian_path": self.hamiltonian_path,
        }

    def get_hash(self):
        return (
            weisfeiler_lehman_graph_hash(self.graph)
            + f"_{self.start_node}_{self.end_node}"
        )
