import random
from networkx import weisfeiler_lehman_graph_hash
from matplotlib import pyplot as plt
import networkx as nx
import pickle

random.seed(3)


def generate_clique_graph(k=5, num_nodes=20, edge_prob=0.1):
    """
    Generate a graph with a k-sized clique and additional random nodes and edges.

    Parameters:
        k (int): Size of the clique.
        num_nodes (int): Total number of nodes in the graph.
        edge_prob (float): Probability of edges between non-clique nodes.

    Returns:
        networkx.Graph: A graph with a central clique and additional random nodes and edges.
    """
    G = nx.complete_graph(k)

    # Add remaining nodes
    other_nodes = list(range(k, num_nodes))
    G.add_nodes_from(other_nodes)

    # Add random edges between other nodes
    for i in other_nodes:
        for j in other_nodes:
            if i < j and random.random() < edge_prob:
                G.add_edge(i, j)

    # Add edges between clique nodes and other nodes
    for i in other_nodes:
        if random.random() < edge_prob:
            G.add_edge(i, random.choice(range(k)))

    return G


def add_random_nodes_and_edges(graph, k, num_additional_nodes):
    """
    Add random nodes and edges to the graph.

    Parameters:
        graph (networkx.Graph): The initial graph.
        k (int): Size of the initial clique.
        num_additional_nodes (int): Number of additional nodes to add.

    Returns:
        networkx.Graph: The graph with additional nodes and edges.
    """
    for i in range(1, num_additional_nodes):
        graph.add_node(i + k)
        graph.add_edge(random.randint(0, k), i + k)
        graph.add_edge(random.randint(0, k), i + k)
    return graph


def generate_kclique_data_set(max_k=5):
    """
    Generate a dataset of graphs with k-sized cliques.

    Parameters:
        max_k (int): Maximum size of the clique.

    Returns:
        set: A set of tuples containing the graph, the complete graph, and the size of the clique.
    """
    graphs = set()
    graph_already_generated = set()

    for k in range(3, max_k + 1):
        for num_additional_nodes in range(2, 4):
            for _ in range(1000):
                # Create a complete graph of size k
                complete_graph = nx.complete_graph(k)
                graph = complete_graph.copy()

                # Add random nodes and edges to the graph
                graph = add_random_nodes_and_edges(graph, k, num_additional_nodes)

                # Remove self-loops and check connectivity
                if nx.is_connected(graph):
                    graph.remove_edges_from(nx.selfloop_edges(graph))
                    whash = weisfeiler_lehman_graph_hash(graph)
                    if whash not in graph_already_generated:
                        graph_already_generated.add(whash)
                        graphs.add((graph, complete_graph, k))

                # Generate another graph with random nodes and edges
                graph2 = generate_clique_graph(k, k + num_additional_nodes, 0.1)
                whash2 = weisfeiler_lehman_graph_hash(graph2)
                if whash2 not in graph_already_generated and nx.is_connected(graph2):
                    graph_already_generated.add(whash2)
                    graphs.add((graph2, complete_graph, k))

    return graphs


def save_graphs_to_file(graphs, filename):
    """
    Save the generated graphs to a file.

    Parameters:
        graphs (list): List of generated graphs.
        filename (str): The filename to save the graphs.
    """
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)


def save_graph_figures(graphs, output_dir, num_samples=10):
    """
    Save figures of a random sample of graphs to files.

    Parameters:
        graphs (list): List of generated graphs.
        output_dir (str): Directory to save the figures.
        num_samples (int): Number of samples to save.
    """
    for i, (graph, complete_graph, k) in enumerate(random.sample(graphs, num_samples)):
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        nx.draw(graph, ax=ax[0], with_labels=True)
        nx.draw(complete_graph, ax=ax[1], with_labels=True)
        plt.savefig(f"{output_dir}/clique_{i}.png")
        plt.close()


if __name__ == "__main__":
    max_k = 5
    graphs = list(generate_kclique_data_set(max_k))

    print("Number of graphs: ", len(graphs))

    save_graphs_to_file(graphs, "algorithms/kcliques/kclique_data.pkl")
    save_graph_figures(graphs, "algorithms/kcliques/figures")
