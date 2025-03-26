import dimod
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph
import networkx as nx

class VertexCover:
    
    def __init__(self, graph, vertex_cover):
        self.graph = graph
        self.vertex_cover = vertex_cover
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.build_qubo()
    
    
    def build_qubo(self):
        A, B = 2, 1
        Ha = dimod.BinaryQuadraticModel(dimod.BINARY)
        for u, v in self.graph.edges():
            Ha.add_linear(u, -1)
            Ha.add_linear(v, -1)
            Ha.add_interaction(u, v, 1)
            Ha.offset += 1
        Ha.scale(A)
        self.qubo.update(Ha)
        
        Hb = dimod.BinaryQuadraticModel(dimod.BINARY)
        for u in self.graph.nodes():
            Hb.add_linear(u, 1)
        Hb.scale(B)
        self.qubo.update(Hb)

    
    def get_binary_polynomial(self):
        return self.qubo
    

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "vertex_cover": self.vertex_cover            
        }
        
        
    def get_hash(self):
        h = weisfeiler_lehman_graph_hash(nx.Graph(self.vertex_cover))
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{h}"
    
    
    def verify_bitstring(self, bitstring, qubits_to_variables):
        variables_to_qubits = {v: k for k, v in qubits_to_variables.items()}
        for u in self.vertex_cover:
            if bitstring[variables_to_qubits[u]] == 0:
                return False
        for u, v in self.graph.edges():
            if bitstring[variables_to_qubits[u]] == 0 and bitstring[variables_to_qubits[v]] == 0:
                return False
        return True