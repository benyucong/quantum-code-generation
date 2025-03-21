import networkx as nx
import random
import pickle
import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations

def generate_steiner_problem(n_nodes, n_terminals, edge_density=0.3, min_weight=1, max_weight=10, seed=None):
    """
    Generate a random Steiner tree problem instance.
    
    Parameters:
    - n_nodes: Total number of nodes in the graph
    - n_terminals: Number of terminal nodes that must be connected
    - edge_density: Probability of edge creation between any two nodes
    - min_weight, max_weight: Range for random edge weights
    - seed: Random seed for reproducibility
    
    Returns:
    - G: NetworkX graph with weighted edges
    - terminals: Set of terminal nodes
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Ensure valid parameters
    if n_terminals > n_nodes:
        raise ValueError("Number of terminals cannot exceed total number of nodes")
    
    # Create a random graph with the given parameters
    G = nx.gnp_random_graph(n_nodes, edge_density, seed=seed)
    
    # Ensure the graph is connected
    if not nx.is_connected(G):
        # Add edges to make the graph connected
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = random.choice(list(components[i]))
            v = random.choice(list(components[i + 1]))
            G.add_edge(u, v)
    
    # Assign random weights to edges
    for u, v in G.edges():
        G[u][v]['weight'] = random.randint(min_weight, max_weight)
    
    # Select random terminal nodes
    terminals = set(random.sample(list(G.nodes()), n_terminals))
    
    # Mark terminal nodes in the graph
    nx.set_node_attributes(G, False, 'terminal')
    for t in terminals:
        G.nodes[t]['terminal'] = True
    
    return G, terminals

def compute_steiner_tree(G, terminals):
    """
    Compute the minimum Steiner tree for the given graph and terminal nodes.
    This uses the approximation algorithm based on minimum spanning tree of the metric closure.
    
    Parameters:
    - G: NetworkX graph with weighted edges
    - terminals: Set of terminal nodes
    
    Returns:
    - steiner_tree: Subgraph representing the approximated minimum Steiner tree
    - steiner_edges: Edges in the Steiner tree
    - steiner_nodes: Nodes in the Steiner tree (including non-terminal Steiner points)
    """
    # Create the metric closure of terminals
    metric_closure = nx.Graph()
    for u, v in combinations(terminals, 2):
        # Find shortest path between terminal nodes
        if nx.has_path(G, u, v):
            path_length = nx.shortest_path_length(G, u, v, weight='weight')
            metric_closure.add_edge(u, v, weight=path_length, path=nx.shortest_path(G, u, v, weight='weight'))
    
    # Find the minimum spanning tree of the metric closure
    mst_edges = list(nx.minimum_spanning_edges(metric_closure, weight='weight', data=True))
    
    # Collect all edges from the shortest paths
    steiner_edges = set()
    for u, v, data in mst_edges:
        path = data['path']
        for i in range(len(path) - 1):
            steiner_edges.add((path[i], path[i + 1]))
    
    # Create the Steiner tree
    steiner_tree = nx.Graph()
    for u, v in steiner_edges:
        steiner_tree.add_edge(u, v, weight=G[u][v]['weight'])
    
    # Identify Steiner points (non-terminal nodes in the tree)
    #steiner_nodes = set(steiner_tree.nodes()) - terminals

    # Compute steiner tree with netwrokx to double check
    steiner_tree_nx = nx.algorithms.approximation.steinertree.steiner_tree(G, list(terminals))
    assert nx.is_isomorphic(steiner_tree_nx, steiner_tree), "Steiner tree is not the same as the one computed by networkx"
    
    return steiner_tree #list(steiner_edges), list(steiner_nodes)

def compute_optimal_steiner_tree(G, terminals):
    """
    Compute the exact optimal Steiner tree using a brute force approach.
    Warning: This is computationally expensive and only feasible for small instances.
    
    Parameters:
    - G: NetworkX graph with weighted edges
    - terminals: Set of terminal nodes
    
    Returns:
    - optimal_tree: Subgraph representing the optimal Steiner tree
    - optimal_edges: Edges in the optimal Steiner tree
    - optimal_nodes: Nodes in the optimal Steiner tree
    - optimal_weight: Total weight of the optimal tree
    """
    non_terminals = set(G.nodes()) - terminals
    best_tree = None
    best_edges = []
    best_nodes = []
    best_weight = float('inf')
    
    # Try all possible subsets of non-terminal nodes
    for k in range(len(non_terminals) + 1):
        for steiner_points in combinations(non_terminals, k):
            # Construct the subgraph with terminals and current Steiner points
            subgraph_nodes = list(terminals) + list(steiner_points)
            subgraph = G.subgraph(subgraph_nodes)
            
            # Check if all terminals are connected in this subgraph
            if nx.is_connected(subgraph) and all(t in subgraph for t in terminals):
                # Find the minimum spanning tree of this subgraph
                mst = nx.minimum_spanning_tree(subgraph, weight='weight')
                mst_weight = sum(mst[u][v]['weight'] for u, v in mst.edges())
                
                # Update if this is the best tree found so far
                if mst_weight < best_weight:
                    best_weight = mst_weight
                    best_tree = mst
                    best_edges = list(mst.edges())
                    best_nodes = list(steiner_points)
    
    # Compute steiner tree with netwrokx to double check
    steiner_tree_nx = nx.algorithms.approximation.steinertree.steiner_tree(G, list(terminals))
    print("Optimal weight:", best_weight)
    print("Approximate weight:", sum(G[u][v]['weight'] for u, v in steiner_tree_nx.edges()))
    print("Approximate weight:", sum(G[u][v]['weight'] for u, v in best_tree.edges()))
    assert best_weight <=  sum(G[u][v]['weight'] for u, v in steiner_tree_nx.edges()) #nx.is_isomorphic(steiner_tree_nx, best_tree), "Steiner tree is not the same as the one computed by networkx"
    
    return best_tree, best_edges, best_nodes, best_weight

def generate_steiner_dataset(n_instances, n_nodes_range=(10, 20), n_terminals_range=(3, 7), 
                          edge_density=0.3, min_weight=1, max_weight=10, seed=None):
    """
    Generate a dataset of Steiner tree problems with their approximate solutions.
    
    Parameters:
    - n_instances: Number of instances to generate
    - n_nodes_range: Range of total nodes in each graph
    - n_terminals_range: Range of terminal nodes in each graph
    - edge_density, min_weight, max_weight: Parameters for graph generation
    - seed: Random seed for reproducibility
    
    Returns:
    - dataset: List of (G, terminals, steiner_tree, steiner_edges, steiner_nodes) tuples
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    dataset = []
    processed_graphs = set()
    
    for i in range(n_instances):
        # Generate random graph sizes
        n_nodes = random.randint(*n_nodes_range)
        n_terminals = random.randint(*n_terminals_range)
        n_terminals = min(n_terminals, n_nodes - 1)  # Ensure we have at least one non-terminal
        
        # Generate graph and terminals
        G, terminals = generate_steiner_problem(
            n_nodes, n_terminals, edge_density, min_weight, max_weight, seed=seed+i if seed else None
        )
        
        steiner_tree, steiner_edges, steiner_nodes, optimal_weight = compute_optimal_steiner_tree(G, terminals)
        
        graph_hash = nx.weisfeiler_lehman_graph_hash(G, edge_attr='weight')
        steiner_tree_hash = nx.weisfeiler_lehman_graph_hash(steiner_tree, edge_attr='weight')
        total_hash = graph_hash + steiner_tree_hash
        if total_hash in processed_graphs:
            continue
        processed_graphs.add(total_hash)
        
        dataset.append((G, terminals, steiner_tree, optimal_weight))
    
    return dataset

def save_steiner_dataset(dataset, filename="steiner_tree_data.pkl"):
    """Save the generated dataset to a pickle file."""
    with open(filename, "wb") as f:
        pickle.dump(dataset, f)

def visualize_steiner_problem(G, terminals, steiner_tree=None, steiner_edges=None, title=None, ax=None):
    """
    Visualize a Steiner tree problem and its solution.
    
    Parameters:
    - G: Original graph
    - terminals: Set of terminal nodes
    - steiner_tree: Computed Steiner tree (optional)
    - steiner_edges: Edges in the Steiner tree (optional)
    - title: Title for the plot
    - ax: Matplotlib axis to draw on
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    
    pos = nx.spring_layout(G, seed=42)
    
    # Draw the original graph
    nx.draw_networkx_edges(G, pos, alpha=0.2, ax=ax)
    
    # Draw edge weights
    edge_labels = {(u, v): G[u][v]['weight'] for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)
    
    # Draw all nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', ax=ax)
    
    # Highlight terminal nodes
    nx.draw_networkx_nodes(G, pos, nodelist=list(terminals), node_color='red', ax=ax)
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos, ax=ax)
    
    # Draw the Steiner tree if provided
    if steiner_edges:
        nx.draw_networkx_edges(G, pos, edgelist=steiner_edges, edge_color='red', width=2, ax=ax)
    
    if title:
        ax.set_title(title)
    ax.axis('off')
    
    return ax

def visualize_steiner_dataset(dataset, n_samples=5, output_dir="steiner_figures"):
    """Visualize a sample of the generated Steiner tree problems."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Select a random sample from the dataset
    samples = random.sample(dataset, min(n_samples, len(dataset)))
    
    for i, (G, terminals, steiner_tree, optimal_weight) in enumerate(samples):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Visualize original problem
        visualize_steiner_problem(G, terminals, title=f"Problem {i+1}: {len(G.nodes())} nodes, {len(terminals)} terminals", ax=ax1)
        
        title = f"\nOptimal Weight: {optimal_weight}"
        visualize_steiner_problem(G, terminals, steiner_edges=steiner_tree.edges(), 
                                    title=title, ax=ax2)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/steiner_problem_{i+1}.png")
        plt.close()

def verify_steiner_solutions(dataset):
    """
    Verify that the computed Steiner trees are valid solutions.
    
    Returns:
    - Dict with verification results
    """
    results = {"valid": 0, "invalid": 0, "optimal_matches": 0}
    
    for G, terminals, steiner_tree, optimal_weight in dataset:
        # Check if all terminals are in the Steiner tree
        terminals_in_tree = all(t in steiner_tree.nodes() for t in terminals)
        
        # Check if the Steiner tree is connected
        is_connected = nx.is_connected(steiner_tree)
        
        # Check if the Steiner tree is actually a tree (no cycles)
        is_tree = nx.is_tree(steiner_tree)
        
        if terminals_in_tree and is_connected and is_tree:
            results["valid"] += 1
        else:
            results["invalid"] += 1
        
        approx_weight = sum(G[u][v]['weight'] for u, v in steiner_tree.edges())
        if abs(approx_weight - optimal_weight) < 1e-6:
            results["optimal_matches"] += 1
    
    return results

if __name__ == "__main__":

    # Generate a few small instances for exact solutions
    dataset = generate_steiner_dataset(
        n_instances=100,
        n_nodes_range=(3, 5),
        n_terminals_range=(3, 5),
        edge_density=0.3,
        min_weight=1,
        max_weight=10,
        seed=0
    )
    
    # Verify solutions
    verification = verify_steiner_solutions(dataset)
    print(f"Verification results: {verification}")
    
    # Save the dataset
    save_steiner_dataset(dataset, "algorithms/steiner_tree/steiner_tree_data.pkl")
    
    # Visualize some examples
    visualize_steiner_dataset(dataset, n_samples=30, output_dir="algorithms/steiner_tree/figures")
    
    print(f"Generated {len(dataset)} Steiner tree problems")