import pickle
import random
import networkx as nx
import numpy as np
from networkx import weisfeiler_lehman_graph_hash
import matplotlib.pyplot as plt

random.seed(0)


def generate_graph_with_components(n, min_size=5, max_size=10, edge_prob=0.5):
    G = nx.Graph()
    components = []
    node_offset = 0  # To ensure unique node labels

    while len(components) < n:
        size = random.randint(min_size, max_size)
        component = nx.erdos_renyi_graph(size, edge_prob)

        # Relabel nodes uniquely
        mapping = {node: node + node_offset for node in component.nodes()}
        component = nx.relabel_nodes(component, mapping)

        if nx.is_connected(component):
            # Add component to the main graph
            G.add_nodes_from(component.nodes())
            G.add_edges_from(component.edges())
            components.append(component)
            node_offset += size

    return G, components


def pick_random_node(components):
    component = random.choice(components)  # Pick a random component
    node = random.choice(list(component.nodes()))  # Pick a random node
    return node


def generate_graphs(max_nodes=18, min_components=2, max_components=8, iterations=100):
    graphs = []
    graph_hashes = []

    for n_components in range(min_components, max_components + 1):
        max_component_size = np.floor(max_nodes / n_components)
        for _ in range(iterations):
            G, components = generate_graph_with_components(
                n_components,
                min_size=2,
                max_size=int(max_component_size),
                edge_prob=0.5,
            )
            node = pick_random_node(components)
            graph_hash = weisfeiler_lehman_graph_hash(G)
            if graph_hash not in graph_hashes:
                graphs.append((G, node, components))
                graph_hashes.append(graph_hash)

    return graphs


def save_graphs(graphs, filename):
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)
    print(f"Saved the graphs to {filename}")


def visualize_graphs(
    graphs, num_graphs=10, output_dir="algorithms/connected_components/figures"
):
    for i in range(num_graphs):
        G, node, components = random.choice(graphs)
        plt.figure()
        nx.draw(G, with_labels=True, font_weight="bold")
        plt.title(
            f"Graph with {len(G)} nodes and {len(components)} components\nEdge: {node}"
        )
        plt.savefig(f"{output_dir}/graph_{i}.png")
        plt.close()


if __name__ == "__main__":
    max_nodes, min_components, max_components, iterations = 18, 2, 6, 100
    graphs = generate_graphs(max_nodes, min_components, max_components, iterations)
    print(f"Generated {len(graphs)} unique graphs")
    save_graphs(graphs, "algorithms/connected_components/connected_components_data.pkl")
    visualize_graphs(graphs)
