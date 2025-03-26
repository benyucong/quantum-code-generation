import pickle
import networkx as nx
import random
import matplotlib.pyplot as plt
from networkx import weisfeiler_lehman_graph_hash
import itertools
from networkx.algorithms import approximation


random.seed(0)

def generate_graph(n_nodes: int, edge_density: float = 0.3):
    """
    Generates an undirected graph with specified properties suitable for the edge cover problem.
    
    Parameters:
    - n_nodes: Number of nodes in the graph.
    - edge_density: Probability of adding an edge between two nodes.
    
    Returns:
    - G: The generated undirected graph.
    """
    G = nx.Graph()
    nodes = list(range(n_nodes))
    G.add_nodes_from(nodes)
    
    # Add edges with the given density
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if random.random() < edge_density:
                G.add_edge(i, j)
    
    # Ensure the graph is connected and has no isolated nodes
    # (edge cover only exists if there are no isolated nodes)
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            # Connect components by adding an edge
            node1 = random.choice(list(components[i]))
            node2 = random.choice(list(components[i + 1]))
            G.add_edge(node1, node2)
    
    # Check for isolated nodes and connect them
    for node in G.nodes():
        if G.degree(node) == 0:
            # Connect to a random non-isolated node
            other_nodes = [n for n in G.nodes() if G.degree(n) > 0]
            if other_nodes:
                G.add_edge(node, random.choice(other_nodes))
            else:
                # If all nodes are isolated, connect to the next node
                next_node = (node + 1) % n_nodes
                G.add_edge(node, next_node)
    
    return G

def find_minimum_edge_cover(G):
    # Use NetworkX's algorithm for larger graphs
    edge_cover = nx.algorithms.min_edge_cover(G)
    return set(edge_cover), len(edge_cover)

def generate_networks(max_nodes=14, num_networks=1000):
    """
    Generate a collection of graphs with different properties.
    
    Returns a list of tuples containing:
    - The graph
    - Minimum edge cover
    - Size of the minimum edge cover
    """
    networks = []
    generated_networks = set()
    
    for n_nodes in range(3, max_nodes + 1, 1):
        for _ in range(num_networks):
            edge_density = random.uniform(0.2, 0.5)
            
            G = generate_graph(n_nodes, edge_density)
            
            # Skip networks that have been generated before
            h = weisfeiler_lehman_graph_hash(G)
            
            if h in generated_networks:
                continue
            
            generated_networks.add(h)
            
            # Find the minimum edge cover
            try:
                edge_cover, cover_size = find_minimum_edge_cover(G)
                networks.append((
                    G, edge_cover, cover_size
                ))
            except ValueError:
                # Skip graphs with isolated vertices
                continue
    
    return networks

def save_networks(networks, filename="edge_cover_data.pkl"):
    """Save generated networks to a pickle file."""
    with open(filename, "wb") as f:
        pickle.dump(networks, f)

def visualize_networks(networks, output_dir="figures"):
    """Visualize a sample of the generated networks."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample some networks to visualize
    samples = random.sample(networks, min(30, len(networks)))
    
    for i, (G, edge_cover, cover_size) in enumerate(samples):
        plt.figure(figsize=(10, 8))
        
        pos = nx.spring_layout(G, seed=42)
        
        # Draw non-cover edges
        non_cover_edges = [e for e in G.edges() if e not in edge_cover and (e[1], e[0]) not in edge_cover]
        nx.draw_networkx_edges(G, pos, edgelist=non_cover_edges, edge_color='gray', width=1)
        
        # Draw cover edges
        nx.draw_networkx_edges(G, pos, edgelist=edge_cover, edge_color='red', width=2)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=700)
        nx.draw_networkx_labels(G, pos)
        
        title = f"Graph with Minimum Edge Cover\nNodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}, Cover Size: {cover_size}"
        plt.title(title)
        plt.savefig(f"{output_dir}/edge_cover_{i}.png")
        plt.close()

def verify_edge_covers(networks):
    """Verify that the found edge covers are valid."""
    results = {"valid": 0, "invalid": 0}
    
    for G, edge_cover, cover_size in networks:
        # Check if it's a valid edge cover
        is_valid = True
        for node in G.nodes():
            # Check if the node is incident to at least one edge in the cover
            if not any((node == u or node == v) for u, v in edge_cover):
                is_valid = False
                break
        
        if is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1
    
    return results

def analyze_networks(networks):
    """Analyze the properties of the generated networks."""
    analysis = {
        "avg_nodes": 0,
        "avg_edges": 0,
        "avg_cover_size": 0,
        "avg_cover_ratio": 0,  # cover size / number of edges
        "min_cover_ratio": float('inf'),
        "max_cover_ratio": 0
    }
    
    for G, edge_cover, cover_size in networks:
        analysis["avg_nodes"] += G.number_of_nodes()
        analysis["avg_edges"] += G.number_of_edges()
        analysis["avg_cover_size"] += cover_size
        
        cover_ratio = cover_size / G.number_of_edges()
        analysis["avg_cover_ratio"] += cover_ratio
        analysis["min_cover_ratio"] = min(analysis["min_cover_ratio"], cover_ratio)
        analysis["max_cover_ratio"] = max(analysis["max_cover_ratio"], cover_ratio)
    
    if networks:
        n = len(networks)
        analysis["avg_nodes"] /= n
        analysis["avg_edges"] /= n
        analysis["avg_cover_size"] /= n
        analysis["avg_cover_ratio"] /= n
    
    return analysis

def get_edge_cover_problem(networks, idx=None):
    """
    Extract an edge cover problem from the networks.
    
    Parameters:
    - networks: List of generated network tuples
    - idx: Optional index to select a specific network (random if None)
    
    Returns:
    - A dictionary containing the graph and the edge cover solution
    """
    if idx is None:
        idx = random.randint(0, len(networks) - 1)
    
    G, edge_cover, cover_size = networks[idx]
    
    # Create a problem instance
    problem = {
        "graph": G,
        "edge_cover": edge_cover,
        "cover_size": cover_size
    }
    
    return problem

if __name__ == "__main__":
    networks = generate_networks(max_nodes=10, num_networks=1000)
    print(f"Generated {len(networks)} graphs for the edge cover problem")
    
    # Verify the networks
    verification = verify_edge_covers(networks)
    print(f"Verification results: {verification}")
    
    # Analyze the networks
    analysis = analyze_networks(networks)
    print(f"Network analysis: {analysis}")
    
    # Save and visualize
    save_networks(networks, "algorithms/edge_cover/edge_cover_data.pkl")
    visualize_networks(networks, "algorithms/edge_cover/figures")
    
    # Extract a sample edge cover problem
    sample_problem = get_edge_cover_problem(networks)
    print(f"Sample edge cover problem: nodes={sample_problem['graph'].number_of_nodes()}, "
          f"edges={sample_problem['graph'].number_of_edges()}, "
          f"cover size={sample_problem['cover_size']}")