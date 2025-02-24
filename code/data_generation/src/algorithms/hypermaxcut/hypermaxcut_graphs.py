import pickle

from src.algorithms.hypermaxcut.hypergraph import generate_random_hypergraph


def generate_hypergraphs(min_num_nodes=3, max_num_nodes=10):
    existing_hypergraphs = set()
    for n_nodes in range(min_num_nodes, max_num_nodes):
        max_num_hyperedges = n_nodes * (n_nodes - 1) // 2
        for n_hyperedges in range(1, max_num_hyperedges):
            for max_edge_size in range(2, n_nodes):
                random_hypergraph = generate_random_hypergraph(
                    n_nodes, n_hyperedges, max_edge_size
                )
                if random_hypergraph not in existing_hypergraphs:
                    existing_hypergraphs.add(random_hypergraph)
    return existing_hypergraphs


def save_graphs(graphs, filename):
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)
    print(f"Saved the graphs to {filename}")


if __name__ == "__main__":
    min_num_nodes, max_num_nodes = 3, 18
    graphs = generate_hypergraphs(min_num_nodes, max_num_nodes)
    print(f"Generated {len(graphs)} unique graphs")
    save_graphs(graphs, "algorithms/hypermaxcut/hypermaxcut_data.pkl")
