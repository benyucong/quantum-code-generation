import dimod
from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph

def append_dict(d, key, value):
    if key not in d:
        d[key] = value
    else:
        d[key] += value


# https://ieeexplore.ieee.org/document/9224181


class MinCut:
    def __init__(self, graph, source, sink, cut_value, cut_edges) -> None:
        self.graph = graph
        self.source = source
        self.sink = sink
        self.cut_value = cut_value
        self.cut_edges = cut_edges

        self.alpha_st = sum([data["capacity"] for _, _, data in self.graph.out_edges(self.source, data=True)]) + 1

        linear = {}
        quadratic = {}
        # x_source - x_source * x_target is 1 if the edge is in the cut
        for source, target in graph.edges():
            capacity = graph[source][target]["capacity"]
            append_dict(linear, source, capacity)
            append_dict(quadratic, (source, target), -capacity)

        append_dict(linear, self.source, -self.alpha_st)
        append_dict(quadratic, (self.source, self.sink), self.alpha_st)

        self.bqm = dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)

    def get_binary_polynomial(self):
        return self.bqm
    
    def verify_bitstring(self, bitstring, qubits_to_variables):
        variables_to_qubits = {qubits_to_variables[qubit]: qubit for qubit in qubits_to_variables}
        for edge in self.graph.edges():
            s, t = edge[0], edge[1]
            s_qubit, t_qubit = variables_to_qubits[s], variables_to_qubits[t]
            edge_in_cut = int(bitstring[s_qubit]) - int(bitstring[s_qubit]) * int(bitstring[t_qubit])
            if edge_in_cut == 0 and edge in self.cut_edges:
                return False
            if edge_in_cut == 1 and edge not in self.cut_edges:
                return False
        return True

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "source": self.source,
            "sink": self.sink,
            "cut_value": self.cut_value,
            "cut_edges": self.cut_edges
        }
    
    def get_hash(self):
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{self.source}_{self.sink}"
