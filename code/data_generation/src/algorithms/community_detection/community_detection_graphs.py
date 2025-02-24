import random
import pickle
from matplotlib import pyplot as plt
import networkx as nx
from networkx import weisfeiler_lehman_graph_hash

random.seed(4)


def generate_community_graph(
    num_communities=3, community_size=2, intra_prob=0.7, inter_prob=0.05
):
    """
    Generate a graph with multiple communities.

    Parameters:
        num_communities (int): Number of communities.
        community_size (int): Number of nodes per community.
        intra_prob (float): Probability of intra-community edges.
        inter_prob (float): Probability of inter-community edges.

    Returns:
        networkx.Graph: A graph with community structure.
    """
    G = nx.Graph()
    communities = []
    node_offset = 0

    # Create communities with dense intra-community edges
    for _ in range(num_communities):
        nodes = list(range(node_offset, node_offset + community_size))
        G.add_nodes_from(nodes)
        communities.append(nodes)

        for i in nodes:
            for j in nodes:
                if i < j and random.random() < intra_prob:
                    G.add_edge(i, j)

        node_offset += community_size

    # Create sparse inter-community edges
    for i in range(num_communities):
        for j in range(i + 1, num_communities):
            for node_i in communities[i]:
                for node_j in communities[j]:
                    if random.random() < inter_prob:
                        G.add_edge(node_i, node_j)

    return G


def generate_community_graphs(max_n_cliques=5, max_clique_size=5):
    """
    Generate a set of community graphs.

    Parameters:
        max_n_cliques (int): Maximum number of cliques.
        max_clique_size (int): Maximum size of each clique.

    Returns:
        set: A set of generated community graphs. Set of tuples (graph, num_of_communities, size_of_communities).
    """
    graphs = set()
    graph_already_generated = set()

    for l in range(2, max_n_cliques + 1):
        for k in range(2, max_clique_size + 1):
            for graph_func in [
                nx.connected_caveman_graph,
                nx.ring_of_cliques,
                nx.windmill_graph,
            ]:
                graph = graph_func(l, k)
                graph_hash = weisfeiler_lehman_graph_hash(graph)

                if graph_hash not in graph_already_generated and nx.is_connected(graph):
                    graphs.add((graph, l, k))
                    graph_already_generated.add(graph_hash)

            for _ in range(100):
                # Custom funcion to generate even more community graphs
                graph = generate_community_graph(l, k)
                graph_hash = weisfeiler_lehman_graph_hash(graph)

                if graph_hash not in graph_already_generated and nx.is_connected(graph):
                    graphs.add((graph, l, k))
                    graph_already_generated.add(graph_hash)

    return graphs


def save_graphs(graphs, filename):
    """
    Save the generated graphs to a file.

    Parameters:
        graphs (list): List of generated graphs.
        filename (str): File path to save the graphs.
    """
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)


def plot_sample_graphs(
    graphs, sample_size=10, output_dir="algorithms/community_detection/figures"
):
    """
    Plot a random sample of graphs and save them to files.

    Parameters:
        graphs (list): List of generated graphs.
        sample_size (int): Number of graphs to sample and plot.
        output_dir (str): Directory to save the plotted graphs.
    """
    for i, (graph, l, k) in enumerate(random.sample(graphs, sample_size)):
        plt.figure(figsize=(10, 5))
        nx.draw(graph, with_labels=True)
        plt.savefig(f"{output_dir}/cd_{i}.png")
        plt.close()


if __name__ == "__main__":
    max_n_cliques, max_size = 5, 5
    graphs = list(generate_community_graphs(max_n_cliques, max_size))

    print("Number of graphs: ", len(graphs))

    save_graphs(graphs, "algorithms/community_detection/community_detection_data.pkl")
    plot_sample_graphs(graphs)
