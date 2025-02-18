"""
Class representing a hypergraph
"""


class HyperGraph:
    def __init__(self, nodes=None, edges=None):
        """
        Initialize a HyperGraph with optional nodes and edges.

        :param nodes: An optional iterable of nodes.
        :param edges: An optional iterable of edges, where each edge is
                      an iterable of nodes.
        """
        self.nodes = set()
        self.edges = set()

        if nodes:
            self.add_nodes(nodes)

        if edges:
            for edge in edges:
                self.add_edge(edge)

    def add_node(self, node):
        """
        Add a single node to the HyperGraph.
        """
        self.nodes.add(node)

    def add_nodes(self, node_iterable):
        """
        Add multiple nodes at once from an iterable (e.g. list, set, etc.).
        """
        self.nodes.update(node_iterable)

    def add_edge(self, node_collection):
        """
        Add an edge (a collection of nodes). Any iterable of nodes is valid.
        """
        edge_set = frozenset(node_collection)
        # Ensure the hypergraph knows about these nodes:
        self.nodes.update(edge_set)
        self.edges.add(edge_set)

    def remove_node(self, node):
        """
        Remove a node from the HyperGraph, along with any edges that contain it.
        """
        if node in self.nodes:
            self.nodes.remove(node)
            # Remove any edges that contain the node:
            self.edges = {e for e in self.edges if node not in e}
        else:
            raise ValueError(f"Node {node} not in HyperGraph")

    def remove_edge(self, node_collection):
        """
        Remove a specific edge from the HyperGraph.
        `node_collection` can be any iterable of nodes (or the exact frozenset).
        """
        edge_set = frozenset(node_collection)
        if edge_set in self.edges:
            self.edges.remove(edge_set)
        else:
            raise ValueError(f"Edge {edge_set} not in HyperGraph")

    def get_nodes(self):
        """
        Return a set of all nodes.
        """
        return set(self.nodes)

    def get_edges(self):
        """
        Return a set of frozensets, each representing one edge.
        """
        return set(self.edges)

    def get_n_nodes(self):
        """
        Returns the number of nodes in the hypergraph.

        Returns:
            int: The number of nodes.
        """
        return len(self.nodes)

    def get_n_edges(self):
        """
        Returns the number of edges in the hypergraph.

        Returns:
            int: The number of edges.
        """
        return len(self.edges)

    def get_signature(self):
        """
        Compute a deterministic, hash-based signature for the HyperGraph.
        This can be used to identify or compare HyperGraphs.

        :return: A hash value representing the graph's state.
        """
        sorted_nodes = sorted(self.nodes)
        sorted_edges = sorted([tuple(sorted(e)) for e in self.edges])

        full_graph = (tuple(sorted_nodes), tuple(sorted_edges))
        return hash(full_graph)

    def __str__(self):
        """
        Return a string representation of the HyperGraph.
        """
        return (
            f"HyperGraph with {len(self.nodes)} nodes and {len(self.edges)} edges.\n"
            f"Nodes: {self.nodes}\n"
            f"Edges: {self.edges}"
        )

    def __getstate__(self):
        """
        Return the state of the HyperGraph for pickling.
        """
        return self.__dict__.copy()

    def __setstate__(self, state):
        """
        Restore the HyperGraph's state from unpickling.
        """
        self.__dict__.update(state)

    def to_dict(self):
        """
        Convert the HyperGraph to a JSON-serializable dictionary.
        Sets are converted to sorted lists.
        """
        return {
            "nodes": sorted(list(self.nodes)),
            "edges": [sorted(list(edge)) for edge in self.edges],
        }
