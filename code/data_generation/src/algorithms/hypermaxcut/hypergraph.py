import random
random.seed(42)
from typing import List, Set, Tuple

class Hypergraph:
    def __init__(self, nodes: List[int], hyperedges: List[Set[int]]):
        self.nodes = nodes
        self.hyperedges = hyperedges
        self.n_nodes = len(nodes)

    def add_hyperedge(self, hyperedge: Set[int]):
        self.hyperedges.append(hyperedge)

    def __repr__(self):
        return f"Hypergraph(nodes={self.nodes}, hyperedges={self.hyperedges})"

    def hypergraph_signature(self) -> Tuple:
        """
        Creates a hashable representation (signature) of the hypergraph.
        """
        hyperedges_signature = tuple(sorted(map(frozenset, self.hyperedges)))
        return (tuple(self.nodes), hyperedges_signature)

    def __eq__(self, other):
        if not isinstance(other, Hypergraph):
            return NotImplemented
        return self.hypergraph_signature() == other.hypergraph_signature()

    def __hash__(self):
        return hash(self.hypergraph_signature())
    
    def __dict__(self):
        json_edges = [list(edge) for edge in self.hyperedges]
        return {"nodes": self.nodes, "hyperedges": json_edges}
    
    def __getstate__(self):
        # Return the state to be pickled
        return self.__dict__()

    def __setstate__(self, state):
        # Restore the state from the unpickled state
        self.nodes = state["nodes"]
        self.hyperedges = [set(edge) for edge in state["hyperedges"]]
        self.n_nodes = len(self.nodes)

def generate_random_hypergraph(num_nodes: int, num_hyperedges: int, max_edge_size: int) -> Hypergraph:
    nodes = list(range(num_nodes))
    hyperedges = []

    for _ in range(num_hyperedges):
        edge_size = random.randint(2, max_edge_size)
        hyperedge = set(random.sample(nodes, edge_size))
        # Check that the hyperedge is not a subset of any other hyperedge
        if not any(hyperedge.issubset(h) or h.issubset(hyperedge) for h in hyperedges):
            hyperedges.append(hyperedge)
    
    # Verify that every node is in at least one hyperedge
    for node in nodes:
        if not any(node in h for h in hyperedges):
            node2 = random.choice([n for n in nodes if n!=node])
            hyperedge = set([node, node2])
            hyperedges.append(hyperedge)

    return Hypergraph(nodes, hyperedges)