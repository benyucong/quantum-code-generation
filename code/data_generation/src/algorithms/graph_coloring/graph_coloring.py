import dimod


class GraphColoring:
    def __init__(self, graph, colors):
        self.graph = graph
        self.colors = colors
        self.coloring = {}
        self.bqm = dimod.BinaryQuadraticModel(dimod.BINARY)

        # Add constraints
        self.one_color_per_node()
        self.adjacent_nodes_have_different_colors()

    def one_color_per_node(self):
        for node in self.graph.nodes():
            vars = [(node, colors) for colors in range(self.colors)]
            constraint = dimod.generators.combinations(vars, 1, strength=1)
            self.bqm.update(constraint)

    def adjacent_nodes_have_different_colors(self):
        quadratic = {}
        for source, target in self.graph.edges():
            for color in range(self.colors):
                if ((source, color), (target, color)) in quadratic:
                    quadratic[((source, color), (target, color))] += 1
                else:
                    quadratic[((source, color), (target, color))] = 1
        self.bqm.update(dimod.BinaryQuadraticModel({}, quadratic, 0, dimod.BINARY))

    def get_binary_polynomial(self):
        return self.bqm
