import itertools
import networkx as nx
import dimod
import numpy as np

def directed_graph_to_unit_multigraph(graph):
    M = nx.MultiDiGraph()
    for u, v, data in graph.edges(data=True):
        for i in range(data['capacity']):
            M.add_edge(u, v, capacity=1, key=(u, v, i))
    return M

def append_dict(d, key, value):
    if key not in d:
        d[key] = value
    else:
        d[key] += value

def combinations_with_variables(list_of_pos_vars, list_of_neg_vars):
    all_vars = list_of_pos_vars + list_of_neg_vars
    pairs = list(itertools.combinations(all_vars, 2))
    all_pairs = pairs + [(x, x) for x in all_vars]
    linear = {}
    quadratic = {}
    for (x, y) in all_pairs:
        if x == y:
            append_dict(linear, x, 1)
        elif x in list_of_pos_vars and y in list_of_pos_vars:
            append_dict(quadratic, (x, y), 2)
        elif x in list_of_neg_vars and y in list_of_neg_vars:
            append_dict(quadratic, (x, y), 2)
        else:
            append_dict(quadratic, (x, y), -2)
    return dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)


def integer_to_binary_var(source_i, target_j, capacity, scaler = 1):
    """ Variable that can encode integer values between 0 and x """
    M = int(np.floor(np.log2(capacity)))
    linear = {}
    for i in range(M - 1):
        linear[(source_i, target_j, i)] = 2 ** i
    
    linear[(source_i, target_j, M)] = capacity - 2 ** M + 1
    bqm = dimod.BinaryQuadraticModel(linear, {}, 0, dimod.BINARY)
    bqm.scale(scaler)
    return bqm

def multiply_binary_representations(source1, target1, source2, target2, capacity_1, capacity_2, scaler = 1):
    quadratic = {}
    M1 = int(np.floor(np.log2(capacity_1)))
    M2 = int(np.floor(np.log2(capacity_2)))
    for i in range(M1 - 1):
        for j in range(M2 - 1):
            append_dict(quadratic, ((source1, target1, i), (source2, target2, j)), 2 ** (i + j))
            
    for i in range(M1 - 1):
        append_dict(quadratic, ((source1, target1, i), (source2, target2, M2)), capacity_2 + 1 - 2 ** M2)
        
    for j in range(M2 - 1):
        append_dict(quadratic, ((source1, target1, M1), (source2, target2, j)), capacity_1 + 1 - 2 ** M1)
    
    append_dict(quadratic, ((source1, target1, M1), (source2, target2, M2)), (capacity_1 + 1 - 2 ** M1)*(capacity_2 + 1 - 2 ** M2))
    bqm = dimod.BinaryQuadraticModel({}, quadratic, 0, dimod.BINARY)
    bqm.scale(scaler)
    return bqm

def combinations_with_binary_variables(list_of_pos_vars_with_capacities, list_of_neg_vars_with_capacities):
    bqm = dimod.BinaryQuadraticModel(dimod.BINARY)
    all_vars = list_of_pos_vars_with_capacities + list_of_neg_vars_with_capacities
    pairs = list(itertools.combinations(all_vars, 2))
    all_pairs = pairs + [(x, x) for x in all_vars]
    
    for (x, y) in all_pairs:
        source1 = x[0]
        target1 = x[1]
        source2 = y[0]
        target2 = y[1]
        capacity_1 = x[2]["capacity"]
        capacity_2 = y[2]["capacity"]
        if x == y:
            bqm1 = integer_to_binary_var(source1, target1, capacity_1, scaler = 1)
        elif x in list_of_pos_vars_with_capacities and y in list_of_pos_vars_with_capacities:
            bqm1 = multiply_binary_representations(source1, target1, source2, target2, capacity_1, capacity_2, scaler = 2)
        elif x in list_of_neg_vars_with_capacities and y in list_of_neg_vars_with_capacities:
            bqm1 = multiply_binary_representations(source1, target1, source2, target2, capacity_1, capacity_2, scaler = 2)
        else:
            bqm1 = multiply_binary_representations(source1, target1, source2, target2, capacity_1, capacity_2, scaler = -2)
        bqm.update(bqm1)
    return bqm