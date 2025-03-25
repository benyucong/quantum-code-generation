import pickle
import networkx as nx
import random
import matplotlib.pyplot as plt

from networkx import weisfeiler_lehman_graph_hash

random.seed(0)


def generate_graph_with_automorphism(n: int, p: float):
    """
    Generates a random graph and an isomorphic graph by applying a node permutation.

    Parameters:
    - n: Number of nodes in the graph.
    - p: Probability of edge creation in an Erdős-Rényi random graph.

    Returns:
    - G: The original graph.
    - G_iso: The isomorphic graph.
    - mapping: Dictionary representing the node automorphism.
    """
    # Generate a random graph
    G = nx.erdos_renyi_graph(n, p)

    # Generate a random permutation of nodes
    nodes = list(G.nodes)
    permuted_nodes = nodes[:]
    random.shuffle(permuted_nodes)
    automorphism = {old: new for old, new in zip(nodes, permuted_nodes)}

    return G, automorphism


def generate_graphs(max_nodes=5):
    graphs = []
    graph_hashes = []
    for n_nodes in range(3, max_nodes):
        for prob in range(4, 10):
            p = prob / 10
            for _ in range(1000):
                G, automorphism = generate_graph_with_automorphism(n_nodes, p)
                graph_hash = weisfeiler_lehman_graph_hash(G)
                if graph_hash not in graph_hashes:
                    graph1 = G
                    graph2 = nx.relabel_nodes(G, automorphism)
                    graphs.append((graph1, graph2, automorphism))
                    graph_hashes.append(graph_hash)
    return graphs


def save_graphs(graphs):
    with open("algorithms/graph_isomorphism/graph_isomorphism_data.pkl", "wb") as f:
        pickle.dump(graphs, f)


def visualize_graphs(graphs):
    # Visualize 10 randomly selected graphs
    for i in range(10):
        graph1, graph2, automorphism = random.choice(graphs)
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.title("Original Graph")
        nx.draw(graph1, with_labels=True, node_color="lightblue", edge_color="gray")
        plt.subplot(1, 2, 2)
        plt.title("Isomorphic Graph")
        nx.draw(graph2, with_labels=True, node_color="lightgreen", edge_color="gray")
        plt.savefig(f"algorithms/graph_isomorphism/figures/graph_{i}.png")


if __name__ == "__main__":
    graphs = generate_graphs()

    print(f"Generated {len(graphs)} unique graphs")

    save_graphs(graphs)
    visualize_graphs(graphs)
