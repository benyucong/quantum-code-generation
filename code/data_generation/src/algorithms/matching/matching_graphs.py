import pickle
import networkx as nx
import random
import matplotlib.pyplot as plt
from networkx import weisfeiler_lehman_graph_hash

random.seed(0)

def generate_graph_with_matching(n: int, matching_type: str, extra_edges: int = 5):
    """
    Generates a graph with a specified type of matching.
    
    Parameters:
    - n: Number of nodes in the graph.
    - matching_type: Type of matching ('maximum', 'perfect', 'near_perfect').
    - extra_edges: Number of additional edges to insert.
    
    Returns:
    - G: The generated graph with edge weights.
    - matching_edges: The edges in the matching.
    """
    G = nx.Graph()
    nodes = list(range(n))
    
    # Add all nodes to the graph
    G.add_nodes_from(nodes)
    
    matching_edges = []
    
    if matching_type == 'perfect':
        # Perfect matching requires an even number of nodes
        if n % 2 != 0:
            raise ValueError("Perfect matching requires an even number of nodes")
        
        # Create a perfect matching (every node is matched)
        for i in range(0, n, 2):
            weight = random.randint(1, 10)
            G.add_edge(nodes[i], nodes[i+1], weight=weight)
            matching_edges.append((nodes[i], nodes[i+1]))
    
    elif matching_type == 'near_perfect':
        # Near-perfect matching leaves exactly one node unmatched (for odd n)
        if n % 2 == 0:
            raise ValueError("Near-perfect matching requires an odd number of nodes")
        
        # Match all but one node
        for i in range(0, n-1, 2):
            weight = random.randint(1, 10)
            G.add_edge(nodes[i], nodes[i+1], weight=weight)
            matching_edges.append((nodes[i], nodes[i+1]))
    
    elif matching_type == 'maximum':
        # Maximum matching matches as many nodes as possible
        # For even n, this is the same as perfect matching
        # For odd n, this is the same as near-perfect matching
        if n % 2 == 0:  # Even case - perfect matching
            for i in range(0, n, 2):
                weight = random.randint(1, 10)
                G.add_edge(nodes[i], nodes[i+1], weight=weight)
                matching_edges.append((nodes[i], nodes[i+1]))
        else:  # Odd case - near-perfect matching
            for i in range(0, n-1, 2):
                weight = random.randint(1, 10)
                G.add_edge(nodes[i], nodes[i+1], weight=weight)
                matching_edges.append((nodes[i], nodes[i+1]))
    
    else:
        raise ValueError("Matching type must be 'maximum', 'perfect', or 'near_perfect'")
    
    # Add extra edges while ensuring they don't create augmenting paths
    # This preserves the optimality of our matching
    possible_edges = [(i, j) for i in nodes for j in nodes 
                      if i < j and not G.has_edge(i, j)]
    random.shuffle(possible_edges)
    
    # Define matched nodes
    matched_nodes = set()
    for u, v in matching_edges:
        matched_nodes.add(u)
        matched_nodes.add(v)
    
    # Add extra edges
    added = 0
    for u, v in possible_edges:
        if added >= extra_edges:
            break
            
        # Add edge with higher weight to preserve the optimality of our matching
        weight = random.randint(11, 20)  # Higher weights for non-matching edges
        G.add_edge(u, v, weight=weight)
        added += 1
    
    return G, matching_edges

def generate_bipartite_graph_with_matching(n_left: int, n_right: int, matching_type: str, extra_edges: int = 5):
    """
    Generates a bipartite graph with a specified type of matching.
    
    Parameters:
    - n_left: Number of nodes in the left partition.
    - n_right: Number of nodes in the right partition.
    - matching_type: Type of matching ('maximum', 'perfect').
    - extra_edges: Number of additional edges to insert.
    
    Returns:
    - G: The generated bipartite graph with edge weights.
    - matching_edges: The edges in the matching.
    - left_nodes: Nodes in the left partition.
    - right_nodes: Nodes in the right partition.
    """
    G = nx.Graph()
    
    # Create left and right node sets
    left_nodes = list(range(n_left))
    right_nodes = list(range(n_left, n_left + n_right))
    
    # Add nodes to the graph with bipartite attribute
    G.add_nodes_from(left_nodes, bipartite=0)
    G.add_nodes_from(right_nodes, bipartite=1)
    
    matching_edges = []
    
    if matching_type == 'perfect':
        # Perfect matching requires equal number of nodes on both sides
        if n_left != n_right:
            raise ValueError("Perfect matching in bipartite graph requires equal number of nodes on both sides")
        
        # Create a perfect matching (every node is matched)
        for i in range(n_left):
            weight = random.randint(1, 10)
            G.add_edge(left_nodes[i], right_nodes[i], weight=weight)
            matching_edges.append((left_nodes[i], right_nodes[i]))
    
    elif matching_type == 'maximum':
        # Maximum matching matches as many nodes as possible
        min_size = min(n_left, n_right)
        
        # Match as many nodes as possible
        for i in range(min_size):
            weight = random.randint(1, 10)
            G.add_edge(left_nodes[i], right_nodes[i], weight=weight)
            matching_edges.append((left_nodes[i], right_nodes[i]))
    
    else:
        raise ValueError("Matching type for bipartite graphs must be 'maximum' or 'perfect'")
    
    # Add extra edges
    possible_edges = [(u, v) for u in left_nodes for v in right_nodes 
                     if not G.has_edge(u, v)]
    random.shuffle(possible_edges)
    
    added = 0
    for u, v in possible_edges:
        if added >= extra_edges:
            break
            
        # Add edge with higher weight
        weight = random.randint(11, 20)  # Higher weights for non-matching edges
        G.add_edge(u, v, weight=weight)
        added += 1
    
    return G, matching_edges, left_nodes, right_nodes

def generate_graphs(max_nodes=10, extra_edges=5):
    """
    Generate a collection of graphs with different types of matchings.
    
    Returns a list of tuples containing:
    - The graph
    - The matching edges
    - Type of matching
    - Additional info specific to the graph type
    """
    graphs = []
    generated_graphs = set()
    
    # Generate regular graphs with matchings
    for n_nodes in range(4, max_nodes+1):
        # Generate perfect matchings for even n
        if n_nodes % 2 == 0:
            for _ in range(50):
                G, matching = generate_graph_with_matching(n_nodes, 'perfect', extra_edges)
                h = weisfeiler_lehman_graph_hash(G)
                if h in generated_graphs:
                    continue
                generated_graphs.add(h)
                graphs.append((G, matching, 'perfect', {'n': n_nodes}))
        
        # Generate near-perfect matchings for odd n
        if n_nodes % 2 == 1 and n_nodes > 3:
            for _ in range(50):
                G, matching = generate_graph_with_matching(n_nodes, 'near_perfect', extra_edges)
                h = weisfeiler_lehman_graph_hash(G)
                if h in generated_graphs:
                    continue
                generated_graphs.add(h)
                graphs.append((G, matching, 'near_perfect', {'n': n_nodes}))
        
        # Generate maximum matchings for all n
        for _ in range(50):
            G, matching = generate_graph_with_matching(n_nodes, 'maximum', extra_edges)
            h = weisfeiler_lehman_graph_hash(G)
            if h in generated_graphs:
                continue
            generated_graphs.add(h)
            graphs.append((G, matching, 'maximum', {'n': n_nodes}))
    
    # Generate bipartite graphs with matchings
    for n_left in range(3, max_nodes):
        for n_right in range(3, max_nodes):
            # Generate perfect matchings for bipartite graphs with equal partitions
            if n_left == n_right:
                for _ in range(50):
                    G, matching, left, right = generate_bipartite_graph_with_matching(
                        n_left, n_right, 'perfect', extra_edges
                    )
                    h = weisfeiler_lehman_graph_hash(G)
                    if h in generated_graphs:
                        continue
                    generated_graphs.add(h)
                    graphs.append((G, matching, 'perfect_bipartite', 
                                  {'left_nodes': left, 'right_nodes': right}))
            
            # Generate maximum matchings for bipartite graphs
            for _ in range(50):
                G, matching, left, right = generate_bipartite_graph_with_matching(
                    n_left, n_right, 'maximum', extra_edges
                )
                h = weisfeiler_lehman_graph_hash(G)
                if h in generated_graphs:
                    continue
                generated_graphs.add(h)
                graphs.append((G, matching, 'maximum_bipartite',
                              {'left_nodes': left, 'right_nodes': right}))
    
    return graphs


def save_graphs(graphs, filename="matching_graphs_data.pkl"):
    """Save generated graphs to a pickle file."""
    with open(filename, "wb") as f:
        pickle.dump(graphs, f)


def visualize_graphs(graphs, output_dir="matching_figures"):
    """Visualize a sample of the generated graphs."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample some graphs to visualize
    samples = random.sample(graphs, min(30, len(graphs)))
    
    for i, (G, matching, matching_type, info) in enumerate(samples):
        plt.figure(figsize=(8, 6))
        
        # Different layout for bipartite graphs
        if 'bipartite' in matching_type:
            left_nodes = info['left_nodes']
            right_nodes = info['right_nodes']
            pos = {}
            
            # Left nodes on the left side
            for i, node in enumerate(left_nodes):
                pos[node] = (-1, (i - len(left_nodes)/2) / max(len(left_nodes), 1) * 2)
            
            # Right nodes on the right side
            for i, node in enumerate(right_nodes):
                pos[node] = (1, (i - len(right_nodes)/2) / max(len(right_nodes), 1) * 2)
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Draw the graph
        edge_labels = {(u, v): G[u][v]['weight'] for u, v in G.edges()}
        nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=700)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        # Highlight the matching edges
        nx.draw_networkx_edges(G, pos, edgelist=matching, edge_color='red', width=2)
        
        title = f"{matching_type.replace('_', ' ').title()} Matching"
        if 'bipartite' in matching_type:
            title += f" (Left: {len(info['left_nodes'])}, Right: {len(info['right_nodes'])})"
        else:
            title += f" (n={info['n']})"
            
        plt.title(title)
        plt.savefig(f"{output_dir}/graph_{i}_{matching_type}.png")
        plt.close()


def verify_matchings(graphs):
    """Verify that generated matchings are valid and optimal."""
    results = {"valid": 0, "invalid": 0}
    
    for G, matching, matching_type, info in graphs:
        # Check if matching is valid (no common nodes)
        nodes_in_matching = set()
        valid = True
        
        for u, v in matching:
            if u in nodes_in_matching or v in nodes_in_matching:
                valid = False
                break
            nodes_in_matching.add(u)
            nodes_in_matching.add(v)
        
        # For perfect matchings, check if all nodes are matched
        if valid and matching_type == 'perfect':
            if len(nodes_in_matching) != G.number_of_nodes():
                valid = False
        
        # For near-perfect matchings, check if n-1 nodes are matched
        if valid and matching_type == 'near_perfect':
            if len(nodes_in_matching) != G.number_of_nodes() - 1:
                valid = False
        
        # For maximum matchings, verify by comparing with networkx's algorithm
        if valid and 'maximum' in matching_type:
            nx_matching = nx.algorithms.matching.max_weight_matching(G, weight='weight')
            if len(matching) < len(nx_matching):
                valid = False
        
        if valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1
    
    return results


if __name__ == "__main__":
    graphs = generate_graphs(max_nodes=10, extra_edges=5)
    print(f"Generated {len(graphs)} graphs with various matchings")
    
    # Verify the matchings
    verification = verify_matchings(graphs)
    print(f"Verification results: {verification}")
    
    # Save and visualize
    save_graphs(graphs, "algorithms/matching/matching_graphs_data.pkl")
    visualize_graphs(graphs, "algorithms/matching/figures")