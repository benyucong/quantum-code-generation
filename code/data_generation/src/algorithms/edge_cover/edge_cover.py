import itertools
import dimod
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph
import networkx as nx
import numpy as np

class EdgeCover:
    
    def __init__(self, graph, edge_cover):
        self.graph = graph
        self.edges = list(self.graph.edges()) #list(set([tuple(edge) for edge in graph.edges()]))
        self.nodes = list(graph.nodes())
        self.edge_cover = [tuple(sorted(edge)) for edge in edge_cover]
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)
        self.build_hubo()
    
    def build_qubo(self):
        A, B = 2*len(self.edges), 1
        
        for edge in self.edges:
            self.qubo.add_linear(edge, 1)
        
        self.qubo.scale(B)
        
        # Every node must be covered by at least one edge in the edge cover
        for node in self.nodes:
            adjacent_edges = [edge for edge in self.edges if node in edge]
            
            #M = int(np.floor(np.log2(len(adjacent_edges))))
            M = len(adjacent_edges)
            integer_vars = [("aux"+ str(node), i) for i in range(M)]
            #v = ("aux"+ str(node), np.log2(len(adjacent_edges) + 1 - 2**M))
            #if v not in integer_vars:
            #    integer_vars.append(v)
                
            bqm = dimod.BinaryQuadraticModel(dimod.BINARY)
            
            for int_var in integer_vars:
                bqm.add_linear(int_var, 3) #*2**(int_var[1]))
            
            for e in adjacent_edges:
                bqm.add_linear(e, -1)
                
            for x, y in itertools.combinations(integer_vars, 2):
                bqm.add_quadratic(x, y, 2) #2**(x[1] + y[1] + 1))
            
            for x, y in itertools.combinations(adjacent_edges, 2):
                bqm.add_quadratic(x, y, 2)
                
            for int_var, edge in itertools.product(integer_vars, adjacent_edges):
                bqm.add_quadratic(int_var, edge, -2) #*2**(int_var[1]))
        
            bqm.scale(A)
            self.qubo.update(bqm)
            
    def build_hubo(self):
        A, B = 2, 1
        
        hubo = dict()
        
        # Every node must be covered by at least one edge in the edge cover
        for node in self.nodes:
            adjacent_edges = [edge for edge in self.edges if node in edge]
            
            for size in range(1, len(adjacent_edges) + 1):
                for subset in itertools.combinations(adjacent_edges, size):
                    v = tuple(sorted(subset))
                    if len(subset) % 2 == 0:
                        if v in hubo:
                            hubo[v] += A
                        else:
                            hubo[v] = A
                    else:
                        if v in hubo:
                            hubo[v] -= A
                        else:
                            hubo[v] = -A
        
        for edge in self.edges:
            v = (tuple(sorted(edge)),)
            if v in hubo:
                hubo[v] += B
            else:
                hubo[v] = B
            
        self.qubo = dimod.BinaryPolynomial(hubo, dimod.BINARY)
        
    
    def get_binary_polynomial(self):
        return self.qubo
    

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "edge_cover": self.edge_cover            
        }
        
    def get_hash(self):
        h = weisfeiler_lehman_graph_hash(nx.Graph(self.edge_cover))
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{h}"
    
    def verify_bitstring(self, bitstring, qubits_to_variables):
        #print("Verifying bitstring:", bitstring)
        #print("Qubits to variables:", qubits_to_variables)
        print("Edge cover:", self.edge_cover)
        variables_to_qubits = {v: k for k, v in qubits_to_variables.items()}
        
        for edge in self.edges:
            if bitstring[variables_to_qubits[edge]] == "1":
                if edge not in self.edge_cover:
                    print("Edge not in edge cover:", edge)
                    return False
                
        for edge in self.edge_cover:
            if bitstring[variables_to_qubits[edge]] == "0":
                print("Edge in edge cover not selected:", edge)
                return False
            
        return True