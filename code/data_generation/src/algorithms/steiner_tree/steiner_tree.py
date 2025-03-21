import itertools
import dimod
from networkx import weisfeiler_lehman_graph_hash
import numpy as np
from networkx.readwrite import json_graph
import networkx as nx

def combinations_with_variables(list_of_vars, fixed_var):
    linear = {}
    quadratic = {}
    linear[fixed_var] = 1
    for var in list_of_vars:
        if var not in linear:
            linear[var] = 1
        else:
            linear[var] += 1
        if (var, fixed_var) not in quadratic:
            quadratic[(var, fixed_var)] = -2
        else:
            quadratic[(var, fixed_var)] -= 2

    var_combs = itertools.combinations(list_of_vars, 2)
    for var_comb in var_combs:
        if var_comb not in quadratic:
            quadratic[var_comb] = 2
        else:
            quadratic[var_comb] += 2
            
    return dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)


class SteinerTree:
    def __init__(self, graph, terminals, steiner_tree, optimal_weight) -> None:
        self.graph = graph
        self.U = terminals
        self.optimal_weight = optimal_weight
        self.steiner_tree = steiner_tree
        self.bqm = dimod.BinaryQuadraticModel.empty(dimod.BINARY)
        self.depth = int(np.ceil(len(graph.nodes()) / 2))
        self.shape_constraint_0()
        self.shape_constraint_1()
        self.shape_constraint_2()
        self.shape_constraint_3()
        self.shape_constraint_4()
        self.shape_constraint_5()
        self.bqm.scale(2)
        self.weight_constraint_0()
        
        # Solve the problem with simulated annealing
        sampler = dimod.SimulatedAnnealingSampler()
        sampleset = sampler.sample(self.bqm, num_reads=1000)
        # Get the best solution
        best_sample = sampleset.first.sample
        best_energy = sampleset.first.energy
        #print("Best sample:")
        #print(best_sample)
        print("Best energy:")
        print(best_energy)
        # Print the solution
        print("Steiner tree edges:")
        steiner_tree = []
        for i in range(1, self.depth):
            for edge in self.graph.edges():
                if best_sample[("edge(" + str(edge) + ")", "level(" + str(i) + ")")] == 1:
                    steiner_tree.append(edge)
                if best_sample[("edge_y(" + str(edge) + ")",)] == 1:
                    steiner_tree.append(edge)
        #print(steiner_tree)
        if not nx.is_isomorphic(
            self.steiner_tree, nx.Graph(steiner_tree)
        ):
            print("The solution is not isomorphic to the correct Steiner tree")
            print(self.steiner_tree.edges())
            print(steiner_tree)

    def shape_constraint_0(self):
        # Exactly one root node
        H0 = dimod.generators.combinations(
            [
                ("node(" + str(node) + ")", "level(" + str(0) + ")")
                for node in self.graph.nodes()
            ],
            1,
            strength=1,
        )
        self.bqm.update(H0)

    def shape_constraint_1(self):
        # Every node appears at exactly one level in the tree if it belongs to the set U
        for node in self.U:
            H1 = dimod.generators.combinations(
                [
                    ("node(" + str(node) + ")", "level(" + str(i) + ")")
                    for i in range(self.depth)
                ],
                1,
                strength=1,
            )
            self.bqm.update(H1)

    def shape_constraint_2(self):
        # If the edge uv appears at the tree, then either u is closer to the root than v ($x_{uv, i} = 1$),
        # or v is closer to the root than u ($x_{vu, i} = 1$)
        for v in self.graph.nodes():
            if v not in self.U:
                list_of_vars = [
                    ("node(" + str(v) + ")", "level(" + str(i) + ")")
                    for i in range(self.depth)
                ]
                H2 = combinations_with_variables(
                    list_of_vars, ("node_y(" + str(v) + ")",)
                )
                self.bqm.update(H2)

    def shape_constraint_3(self):
        # If the node v appears at level i, then exactly one edge uv connects v to a node u at level i
        for node in self.graph.nodes():
            for i in range(1, self.depth):
                list_of_vars = [
                    ("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")
                    for (u, v) in self.graph.edges()
                    if node == v
                ]
                H3 = combinations_with_variables(
                    list_of_vars,
                    ("node(" + str(node) + ")", "level(" + str(i) + ")"),
                )
                self.bqm.update(H3)

    def shape_constraint_4(self):
        # If the edge uv appears at the level i, then the node u appears at level i-1 and the node v appears at level i
        for u, v in self.graph.edges():
            for i in range(1, self.depth):
                linear = {}
                quadratic = {}

                x = ("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")
                
                linear[x] = 2
                
                quadratic[
                    (("node(" + str(u) + ")", "level(" + str(i - 1) + ")"), x)
                ] = -1
                
                quadratic[
                    (("node(" + str(v) + ")", "level(" + str(i) + ")"), x)
                ] = -1

                H5 = dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)
                self.bqm.update(H5)
        
        if True:
            for v, u in self.graph.edges():
                for i in range(1, self.depth):
                    linear = {}
                    quadratic = {}

                    x = ("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")
                    
                    linear[x] = 2
                    
                    quadratic[
                        (("node(" + str(u) + ")", "level(" + str(i - 1) + ")"), x)
                    ] = -1
                    
                    quadratic[
                        (("node(" + str(v) + ")", "level(" + str(i) + ")"), x)
                    ] = -1

                    H5 = dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)
                    self.bqm.update(H5)
                
    def shape_constraint_5(self):
        for u, v in self.graph.edges():
            list_of_vars = [
                    ("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")
                    for i in range(self.depth)
                ] + [
                    ("edge(" + str((v, u)) + ")", "level(" + str(i) + ")") 
                    for i in range(self.depth)
                ]
            H5 = combinations_with_variables(
                list_of_vars, ("edge_y(" + str((u, v)) + ")",)
            )
            self.bqm.update(H5)
            

    def weight_constraint_0(self):
        # Weight of a tree is the sum of the weights of all the selected edges in the tree
        for u, v in self.graph.edges():
            linear = {}
            for i in range(1, self.depth):
                linear[("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")] = 1
            H6 = dimod.BinaryQuadraticModel(linear, {}, 0, dimod.BINARY)
            self.bqm.update(H6)
            
        if True:   
            for v, u in self.graph.edges():
                linear = {}
                for i in range(1, self.depth):
                    linear[("edge(" + str((u, v)) + ")", "level(" + str(i) + ")")] = 1
                H6 = dimod.BinaryQuadraticModel(linear, {}, 0, dimod.BINARY)
                self.bqm.update(H6)

    def get_binary_polynomial(self):
        return self.bqm
    
    def verify_bitstring(self, bitstring, qubits_to_variables):
        steiner_tree = []
        print(qubits_to_variables)
        variables_to_qubits = {v: k for k, v in qubits_to_variables.items()}
        for i in range(1, self.depth):
            for edge in self.graph.edges():
                if bitstring[variables_to_qubits[("edge(" + str(edge) + ")", "level(" + str(i) + ")")]] == "1":
                    steiner_tree.append(edge)
                    
        steiner_nodes = []
        for i in range(self.depth):
            for node in self.graph.nodes():
                if bitstring[variables_to_qubits[("node(" + str(node) + ")", "level(" + str(i) + ")")]] == "1":
                    steiner_nodes.append(node)
        auxiliary_nodes = []
        for edge in self.graph.edges():
            if bitstring[variables_to_qubits[("edge_y(" + str(edge) + ")",)]] == "1":
                auxiliary_nodes.append(edge)
        print("Steiner nodes:")
        print(steiner_nodes)
        print("Steiner tree:")
        print(steiner_tree)
        print("Auxiliary nodes:")
        print(auxiliary_nodes)
        print("Steiner tree edges:")
        print(self.steiner_tree.edges())
        for edge in self.steiner_tree.edges():
            print(edge)
            if edge not in steiner_tree:
                return False
        return True

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "terminals": self.U,
        }
    
    def get_hash(self):
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{self.U}"