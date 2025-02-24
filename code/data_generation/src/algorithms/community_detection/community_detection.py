import dimod
import networkx as nx

colors = ["gray", "blue", "red", "green", "magenta", "yellow", "purple", "black"]


class CommunityDetection:
    def __init__(self, graph, number_of_communities):
        self.graph = graph
        self.number_of_communities = number_of_communities
        self.max_weight = 0
        self.samplesets = {}
        for e in self.graph.edges:
            if "weight" not in self.graph[e[0]][e[1]]:
                self.graph[e[0]][e[1]]["weight"] = 1
            self.max_weight += self.graph[e[0]][e[1]]["weight"]
        self.bqm = dimod.BinaryQuadraticModel(vartype=dimod.BINARY)

        self.constraint_1()
        self.constraint_2()
        self.bqm.normalize()

    def constraint_1(self):
        # Each node belongs to exactly one community
        for node in self.graph.nodes:
            bqm = dimod.generators.combinations(
                [(node, c) for c in range(self.number_of_communities)], 1, strength=10
            )
            self.bqm.update(bqm)

    def constraint_2(self):
        # Maximize the number of edges within communities and
        # minimize the number of edges between communities
        bqm_dict = {}
        A = nx.adjacency_matrix(self.graph).toarray()

        for node1 in self.graph.nodes:
            for node2 in self.graph.nodes:
                for community in range(self.number_of_communities):
                    if (node1, community) != (node2, community):
                        g1 = self.graph.degree(node1, weight="weight")
                        g2 = self.graph.degree(node2, weight="weight")
                        bqm_dict[(node1, community), (node2, community)] = A[node1][
                            node2
                        ] - g1 * g2 / (2 * self.max_weight)

        bqm = dimod.BinaryQuadraticModel(vartype=dimod.BINARY)
        bqm.add_quadratic_from(bqm_dict)
        bqm.scale(-1 / (2 * self.max_weight))
        self.bqm.update(bqm)

    def result_to_colors(self, sample):
        cs = ["white"] * len(self.graph.nodes)
        for i, node in enumerate(self.graph.nodes):
            for k, v in sample.items():
                if k[0] == node and v == 1:
                    cs[i] = colors[k[1]]
        return cs

    def get_binary_polynomial(self):
        return self.bqm
