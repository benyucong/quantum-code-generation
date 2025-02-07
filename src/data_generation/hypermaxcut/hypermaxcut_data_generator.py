import random
from typing import Tuple, Set

from data_generation.data_generator import DataGenerator
from data_generation.hypermaxcut.hypergraph import HyperGraph
from data_generation.hypermaxcut.hypermaxcutsolver import HyperMaxCutSolver


class HyperMaxCutDataGenerator(DataGenerator):
    def __init__(self):
        super().__init__("Hyper MaxCut")
        self.node_range = (4, 10)

    def generate_data(self):
        # First, we generate the hypergraphs
        hypergraphs = self.__generate_hypergraphs()

        for hypergraph in hypergraphs:
            solver = HyperMaxCutSolver(self.n_qubits, self.layers, hypergraph)
            print(solver.solve_vqe())

    def __generate_hypergraphs(self) -> Set[HyperGraph]:
        hypergraphs: Set[HyperGraph] = set()

        for n_nodes in range(self.node_range[1], self.node_range[1] + 1):
            # The maximum amount of hyperedges
            max_hyperedges = n_nodes * (n_nodes - 1) // 2

            for n_hyperedges in range(1, max_hyperedges):
                for max_edge_size in range(2, n_nodes):
                    hypergraph = self.__generate_random_hypergraph(
                        n_nodes, n_hyperedges, max_edge_size
                    )
                    hypergraphs.add(hypergraph)
        return hypergraphs

    def __generate_random_hypergraph(
        self, num_nodes: int, num_hyperedges: int, max_edge_size: int
    ) -> HyperGraph:
        nodes = list(range(num_nodes))
        hyperedges = []

        for _ in range(num_hyperedges):
            edge_size = random.randint(2, max_edge_size)
            hyperedge = set(random.sample(nodes, edge_size))
            # Check that the hyperedge is not a subset of any other hyperedge
            if not any(
                hyperedge.issubset(h) or h.issubset(hyperedge) for h in hyperedges
            ):
                hyperedges.append(hyperedge)

        # Verify that every node is in at least one hyperedge
        for node in nodes:
            if not any(node in h for h in hyperedges):
                node2 = random.choice([n for n in nodes if n != node])
                hyperedge = set([node, node2])
                hyperedges.append(hyperedge)

        return HyperGraph(nodes, hyperedges)
