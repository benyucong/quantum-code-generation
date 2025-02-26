import pickle
import random
import networkx as nx
import matplotlib.pyplot as plt
from networkx import weisfeiler_lehman_graph_hash

random.seed(0)


def generate_k_colorable_graph(n=50, k=3, inter_prob=0.4):
    """
    Generates a k-colorable graph and provides a valid coloring.

    Parameters:
        n (int): Number of nodes in the graph.
        k (int): Number of colors (chromatic number).
        inter_prob (float): Probability of adding an edge between different color sets.

    Returns:
        G (networkx.Graph): The generated k-colorable graph.
        coloring (dict): A valid k-coloring mapping {node: color}.
    """

    assert n >= k, "Number of nodes must be at least k."

    G = nx.Graph()

    nodes_per_set = [n // k] * k
    for i in range(n % k):
        nodes_per_set[i] += 1

    node_sets = []
    node_id = 0
    coloring = {}

    for color in range(k):
        node_set = list(range(node_id, node_id + nodes_per_set[color]))
        node_sets.append(node_set)
        for node in node_set:
            coloring[node] = color
        node_id += nodes_per_set[color]

    for i in range(k):
        for j in range(i + 1, k):
            for u in node_sets[i]:
                for v in node_sets[j]:
                    if random.random() < inter_prob:
                        G.add_edge(u, v)

    return G, coloring


def visualize_graphs(graphs):
    for i in range(10):
        G, colors, coloring = random.choice(graphs)
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(
            G,
            pos,
            node_size=80,
            edge_color="gray",
            with_labels=False,
            node_color=[coloring[node] for node in G.nodes()],
        )
        plt.savefig(f"algorithms/graph_coloring/figures/graph_{i}.png")


def save_graphs_to_file(graphs, filename):
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)


def generate_graphs(max_colors=10, max_nodes=18):
    graphs = []
    graph_hashes = []
    for n_colors in range(3, max_colors + 1):
        for n_nodes in range(n_colors, max_nodes + 1):
            if n_colors * n_nodes < 21:
                for _ in range(2000):
                    for prob in range(2, 10):
                        inter_prob = prob / 10
                        G, coloring = generate_k_colorable_graph(
                            n=n_nodes, k=n_colors, inter_prob=inter_prob
                        )
                        hash_val = weisfeiler_lehman_graph_hash(G)
                        if (
                            len(G.nodes()) == n_nodes
                            and nx.is_connected(G)
                            and hash_val not in graph_hashes
                        ):
                            graphs.append((G, n_colors, coloring))
                            graph_hashes.append(hash_val)
    return graphs


if __name__ == "__main__":
    graphs = generate_graphs()

    print(f"Generated {len(graphs)} unique graphs")

    save_graphs_to_file(graphs, "algorithms/graph_coloring/graph_coloring_data.pkl")
    visualize_graphs(graphs)
