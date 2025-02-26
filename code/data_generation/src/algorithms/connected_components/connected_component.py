import itertools
import dimod

from src.algorithms.qubo_problem import QuadradicUnconstrainedBinaryOptimization


def select_adjacent(variable, variables):
    linear = {}
    quadratic = {}
    coeff = len(variables)
    linear[variable] = coeff**2
    for v in variables:
        linear[v] = 1
        quadratic[(variable, v)] = -2 * coeff

    for v1, v2 in itertools.combinations(variables, 2):
        quadratic[(v1, v2)] = 2

    bqm = dimod.BinaryQuadraticModel(linear, quadratic, 0, dimod.BINARY)
    return bqm


class ConnectedComponentContainingNode(QuadradicUnconstrainedBinaryOptimization):
    def __init__(
        self, graph, fixed_node, description="ConnectedComponentContainingNode"
    ) -> None:
        super().__init__(description=description)

        self.graph = graph
        self.fixed_node = fixed_node
        self.qubo = dimod.BinaryQuadraticModel(dimod.BINARY)

        # Encode the fact: (|adjacent_nodes| * x - sum adjacent_nodes_y)^2 = 0
        for node in self.graph.nodes:
            adjacent_nodes = list(self.graph.adj[node])
            if len(adjacent_nodes) > 0:
                bqm = select_adjacent(node, adjacent_nodes)
                self.qubo.update(bqm)

        # We sum over the variables in order to keep them
        # inactivated if they are not adjacent to the node
        sum_over_vars = dict()
        for node in self.graph.nodes:
            sum_over_vars[node] = 1
        sum_over_vars = dimod.BinaryQuadraticModel(sum_over_vars, {}, 0, dimod.BINARY)
        # sum_over_vars.scale(1/len(self.graph.nodes))
        self.qubo.update(sum_over_vars)
        self.qubo.fix_variable(fixed_node, 1)

    def get_binary_polynomial(self):
        return self.qubo
