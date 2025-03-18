import dimod
from itertools import combinations
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph
import networkx as nx

class Matching:
    """
    Simple formulation in https://arxiv.org/pdf/1910.05129.pdf
    """
    
    def __init__(self, graph, mathcing):
        self.graph = graph
        self.matching = mathcing
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.build_qubo()
    
    def build_qubo(self):
        objective = dimod.BinaryQuadraticModel(dimod.BINARY)
        
        for edge in self.graph.edges:
            if type(edge[0]) == str:
                edge = tuple(sorted(list(edge)))
            if "weight" in self.graph.edges[edge]:
                objective.add_variable(edge, self.graph.edges[edge]["weight"])
            else:
                objective.add_variable(edge, 1)
        
        objective.scale(-1)
        self.qubo.update(objective)
        
        for node in self.graph.nodes:
            adjecent_edges = self.graph.edges(node)
            sorted_adjecent_edges = []
            for edge in adjecent_edges:
                if type(edge[0]) == int and type(edge[1]) == int:
                    if edge[0] > edge[1]:
                        edge = (edge[1], edge[0])
                elif type(edge[0]) == str:
                    edge = tuple(sorted(list(edge)))
                sorted_adjecent_edges.append(edge)
            linear = {}
            quadratic = {}
            for edge in sorted_adjecent_edges:
                linear[edge] = -1
            for edge1, edge2 in combinations(sorted_adjecent_edges, 2):
                quadratic[(edge1, edge2)] = 2
            constraint = dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)
            constraint.scale(len(self.graph.edges))
            self.qubo.update(constraint)
    
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
        return {
            "graph": graph_json,
            "matching": self.matching            
        }
        
    def get_hash(self):
        match_hash = weisfeiler_lehman_graph_hash(nx.Graph(self.matching))
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{match_hash}"