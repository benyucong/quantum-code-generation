import pickle
import networkx as nx
import random
import matplotlib.pyplot as plt
from networkx import weisfeiler_lehman_graph_hash

random.seed(0)


def generate_hamiltonian_graph(n: int, extra_edges: int):
    """
    Generates a graph with a guaranteed Hamiltonian path.

    Parameters:
    - n: Number of nodes in the graph.
    - extra_edges: Number of additional edges to insert.

    Returns:
    - G: The generated graph with edge weights.
    - hamiltonian_path: The minimal Hamiltonian path.
    - start_node: The starting node of the path.
    - end_node: The ending node of the path.
    """
    G = nx.Graph()
    nodes = list(range(n))
    start_node = nodes[0]
    end_node = nodes[-1]

    # Create the minimal Hamiltonian path
    hamiltonian_path = []
    total_weight = 0
    for i in range(n - 1):
        weight = random.randint(1, 10)
        total_weight += weight
        G.add_edge(nodes[i], nodes[i + 1], weight=weight)
        hamiltonian_path.append((nodes[i], nodes[i + 1]))

    # Add extra edges while keeping the Hamiltonian path minimal
    possible_edges = [
        (i, j) for i in nodes for j in nodes if i < j and not G.has_edge(i, j)
    ]
    random.shuffle(possible_edges)

    for _ in range(extra_edges):
        if not possible_edges:
            break
        u, v = possible_edges.pop()
        weight = random.randint(
            total_weight, total_weight + 10
        )  # Slightly higher weights to preserve the minimal path
        G.add_edge(u, v, weight=weight)

    return G, hamiltonian_path, start_node, end_node


def generate_graphs(max_nodes=10, extra_edges=3):
    graphs = []
    generated_graphs = set()
    for n_nodes in range(3, max_nodes):
        for _ in range(2000):
            G, hamiltonian_path, start_node, end_node = generate_hamiltonian_graph(
                n_nodes, extra_edges
            )
            h = (start_node, end_node, weisfeiler_lehman_graph_hash(G))
            if h in generated_graphs:
                continue
            generated_graphs.add(h)
            graphs.append((G, hamiltonian_path, start_node, end_node))
    return graphs


def save_graphs(graphs):
    with open("algorithms/hamiltonian_path/hamiltonian_path_data.pkl", "wb") as f:
        pickle.dump(graphs, f)


def visualize_graphs(graphs):
    for i in range(10):
        G, hamiltonian_path, start_node, end_node = random.choice(graphs)
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        edge_labels = {(u, v): G[u][v]["weight"] for u, v in G.edges()}
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color="lightblue",
            edge_color="gray",
            node_size=700,
        )
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        # Highlight the start and end nodes
        nx.draw_networkx_nodes(
            G, pos, nodelist=[start_node], node_color="red", node_size=700
        )
        nx.draw_networkx_nodes(
            G, pos, nodelist=[end_node], node_color="green", node_size=700
        )
        nx.draw_networkx_edges(
            G, pos, edgelist=hamiltonian_path, edge_color="blue", width=2
        )
        plt.title(f"Start: {start_node}, End: {end_node}")
        plt.savefig(f"algorithms/hamiltonian_path/figures/graph_{i}.png")


if __name__ == "__main__":
    graphs = generate_graphs()
    print(f"Generated {len(graphs)} graphs with Hamiltonian paths")
    # save_graphs(graphs)
    visualize_graphs(graphs)
