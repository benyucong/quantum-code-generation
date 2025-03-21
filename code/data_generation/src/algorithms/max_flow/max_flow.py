import itertools
import dimod
from networkx import weisfeiler_lehman_graph_hash
import numpy as np
from networkx.readwrite import json_graph

# https://ieeexplore.ieee.org/document/9224181


def multiply_polynomials(poly1, poly2):
    """
    Multiply two polynomials represented as dictionaries.

    Parameters:
    - poly1: Dictionary where keys are exponents and values are coefficients
    - poly2: Dictionary where keys are exponents and values are coefficients

    Returns:
    - Dictionary representing the product polynomial
    """
    result = {}

    for var1, coef1 in poly1.items():
        for var2, coef2 in poly2.items():
            if var1 == var2:
                new_var = (var1,)
            else:
                new_var = ((var1,), (var2,))

            new_coef = coef1 * coef2

            if new_var in result:
                result[new_var] = result[new_var] + new_coef
            else:
                result[new_var] = new_coef

    # Remove terms with zero coefficients
    result = {var: coef for var, coef in result.items() if coef != 0}

    return result


class MaxFlow:
    def __init__(self, graph, source, sink, max_flow, flow_dict):
        self.graph = graph
        self.source = source
        self.sink = sink
        self.max_flow = max_flow
        self.flow_dict = flow_dict

        # The integer programming program where the variables are integers
        self.integer_programming_program = {}

        # The binary quadratic model where the variables are binary
        self.bqm = dimod.BinaryQuadraticModel(dimod.BINARY)

        # Sum the capacities of all outgoing edges from the source node
        self.alpha_c = 1 / sum(
            [
                data["capacity"]
                for _, _, data in self.graph.out_edges(self.source, data=True)
            ]
        )

        self.constraint_of_nonaccumulation_integer()
        self.maximize_flow_integer()
        self.integer_program_to_binary_quadratic()

    def constraint_of_nonaccumulation_integer(self):
        for node in self.graph.nodes():
            if node != self.source and node != self.sink:
                # Every variable has the assigend capacity of the edge,
                # then the integer variable encodes the fact how much of this capacity is used in the flow
                incoming_edges = list(self.graph.in_edges(node, data=True))
                outgoing_edges = list(self.graph.out_edges(node, data=True))
                all_edges = incoming_edges + outgoing_edges
                all_variables = list(itertools.combinations(all_edges, 2)) + [
                    (x, x) for x in all_edges
                ]
                for var1, var2 in all_variables:
                    int_var1 = (var1[0], var1[1], var1[2]["capacity"])
                    int_var2 = (var2[0], var2[1], var2[2]["capacity"])

                    if (int_var1, int_var2) not in self.integer_programming_program:
                        self.integer_programming_program[(int_var1, int_var2)] = 0

                    if int_var1 == int_var2:
                        self.integer_programming_program[(int_var1, int_var2)] += 1
                    elif var1 in incoming_edges and var2 in incoming_edges:
                        self.integer_programming_program[(int_var1, int_var2)] += 2
                    elif var1 in outgoing_edges and var2 in outgoing_edges:
                        self.integer_programming_program[(int_var1, int_var2)] += 2
                    else:
                        self.integer_programming_program[(int_var1, int_var2)] -= 2

    def maximize_flow_integer(self):
        for source, target, capacity in self.graph.out_edges(self.source, data=True):
            var = (source, target, capacity["capacity"])
            if (var, var) not in self.integer_programming_program:
                self.integer_programming_program[(var, var)] = 0
            self.integer_programming_program[(var, var)] -= self.alpha_c

    def get_integer_program(self):
        return self.integer_programming_program

    def integer_var_to_bin_vars(self, var, limit):
        M = int(np.floor(np.log2(limit)))
        linear = {}
        for i in range(M):
            linear[(var, i)] = 2**i
        linear[(var, M)] = limit + 1 - 2**M
        return linear

    def integer_program_to_binary_quadratic(self):
        for int_var1, int_var2 in self.integer_programming_program:
            term = dimod.BinaryQuadraticModel(dimod.BINARY)
            coeff = self.integer_programming_program[(int_var1, int_var2)]

            var1 = (int_var1[0], int_var1[1])
            capacity1 = int_var1[2]

            var2 = (int_var2[0], int_var2[1])
            capacity2 = int_var2[2]

            linear1 = self.integer_var_to_bin_vars(var1, capacity1)
            linear2 = self.integer_var_to_bin_vars(var2, capacity2)
            linear = multiply_polynomials(linear1, linear2)

            for bin_var in linear:
                if linear[bin_var] > 0:
                    if len(bin_var) == 2:
                        term.add_interaction(bin_var[0], bin_var[1], linear[bin_var])
                    else:
                        term.add_variable(bin_var, linear[bin_var])

            term.scale(coeff)
            self.bqm.update(term)

    def get_binary_polynomial(self):
        return self.bqm

    def verify_bitstring(self, bitstring, qubits_to_variables):
        flow_mapping = {}
        for qubit in qubits_to_variables:
            edge, exp = qubits_to_variables[qubit][0]
            max_capacity = self.graph[edge[0]][edge[1]]["capacity"]
            M = int(np.floor(np.log2(max_capacity)))

            if bitstring[qubit] == "1":
                if edge[0] not in flow_mapping:
                    flow_mapping[edge[0]] = {}
                    if exp == M:
                        flow_mapping[edge[0]][edge[1]] = max_capacity - 2**M + 1
                    else:
                        flow_mapping[edge[0]][edge[1]] = 2**exp
                else:
                    if edge[1] not in flow_mapping[edge[0]]:
                        if exp == M:
                            flow_mapping[edge[0]][edge[1]] = max_capacity - 2**M + 1
                        else:
                            flow_mapping[edge[0]][edge[1]] = 2**exp
                    else:
                        if exp == M:
                            flow_mapping[edge[0]][edge[1]] = (
                                flow_mapping[edge[0]][edge[1]] + max_capacity - 2**M + 1
                            )
                        else:
                            flow_mapping[edge[0]][edge[1]] = (
                                flow_mapping[edge[0]][edge[1]] + 2**exp
                            )
            else:
                edge, exp = qubits_to_variables[qubit][0]
                if edge[0] not in flow_mapping:
                    flow_mapping[edge[0]] = {}
                    flow_mapping[edge[0]][edge[1]] = 0
                else:
                    if edge[1] not in flow_mapping[edge[0]]:
                        flow_mapping[edge[0]][edge[1]] = 0
                    else:
                        flow_mapping[edge[0]][edge[1]] = (
                            flow_mapping[edge[0]][edge[1]] + 0
                        )

        for source in flow_mapping:
            for target in flow_mapping[source]:
                if flow_mapping[source][target] != self.flow_dict[source][target]:
                    return False
        return True

    def get_problem_data(self):
        graph_json = json_graph.node_link_data(self.graph, edges="edges")
        return {
            "graph": graph_json,
            "source": self.source,
            "sink": self.sink,
            "max_flow": self.max_flow,
            "flow_dict": self.flow_dict,
        }

    def get_hash(self):
        return weisfeiler_lehman_graph_hash(self.graph) + f"_{self.source}_{self.sink}"
