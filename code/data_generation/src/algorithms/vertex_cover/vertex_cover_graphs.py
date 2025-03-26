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
    Generates an undirected graph with specified properties suitable for the vertex cover problem.
    
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
    
    # Ensure the graph is connected
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            # Connect components by adding an edge between random nodes
            node1 = random.choice(list(components[i]))
            node2 = random.choice(list(components[i + 1]))
            G.add_edge(node1, node2)
    
    return G

def find_minimum_vertex_cover(G):
    """
    Finds a minimum vertex cover for the given graph using brute force.
    
    This function uses brute force to find the minimum vertex cover and is only suitable
    for small graphs. For larger graphs, approximation algorithms should be used.
    
    Parameters:
    - G: An undirected graph.
    
    Returns:
    - vertex_cover: A set of nodes forming a minimum vertex cover.
    - cover_size: The size of the minimum vertex cover.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    min_cover = nodes.copy()
    min_cover_size = n
    
    # Check all possible subsets of nodes
    for size in range(n + 1):
        for subset in itertools.combinations(nodes, size):
            cover = set(subset)
            # Check if this is a valid vertex cover
            is_cover = True
            for u, v in G.edges():
                if u not in cover and v not in cover:
                    is_cover = False
                    break
            
            if is_cover and len(cover) < min_cover_size:
                min_cover = cover
                min_cover_size = len(cover)
    
    return min_cover, min_cover_size

def generate_networks(max_nodes=14, num_networks=1000):
    """
    Generate a collection of graphs with different properties.
    
    Returns a list of tuples containing:
    - The graph
    - Minimum vertex cover
    - Size of the minimum vertex cover
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
            
            # For small graphs, find the minimum vertex cover
            if n_nodes <= 14:  # Limit for brute force approach
                vertex_cover, cover_size = find_minimum_vertex_cover(G)
            
                networks.append((
                    G, vertex_cover, cover_size
                ))
    
    return networks

def save_networks(networks, filename="vertex_cover_data.pkl"):
    """Save generated networks to a pickle file."""
    with open(filename, "wb") as f:
        pickle.dump(networks, f)

def visualize_networks(networks, output_dir="figures"):
    """Visualize a sample of the generated networks."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample some networks to visualize
    samples = random.sample(networks, min(30, len(networks)))
    
    for i, (G, vertex_cover, cover_size) in enumerate(samples):
        plt.figure(figsize=(10, 8))
        
        pos = nx.spring_layout(G, seed=42)
        
        # Draw the graph
        nx.draw_networkx_edges(G, pos, edge_color='gray')
        
        # Draw nodes, highlighting the vertex cover
        non_cover_nodes = [node for node in G.nodes() if node not in vertex_cover]
        
        nx.draw_networkx_nodes(G, pos, nodelist=list(vertex_cover), 
                              node_color='lightcoral', node_size=700)
        nx.draw_networkx_nodes(G, pos, nodelist=non_cover_nodes, 
                              node_color='lightblue', node_size=700)
        
        nx.draw_networkx_labels(G, pos)
        
        title = f"Graph with Minimum Vertex Cover\nNodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}, Cover Size: {cover_size}"
        plt.title(title)
        plt.savefig(f"{output_dir}/vertex_cover_{i}.png")
        plt.close()

def verify_vertex_covers(networks):
    """Verify that the found vertex covers are valid."""
    results = {"valid": 0, "invalid": 0}
    
    for G, vertex_cover, cover_size in networks:
        # Check if it's a valid cover
        is_valid = True
        for u, v in G.edges():
            if u not in vertex_cover and v not in vertex_cover:
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
        "avg_cover_ratio": 0,  # cover size / number of nodes
        "min_cover_ratio": float('inf'),
        "max_cover_ratio": 0
    }
    
    for G, vertex_cover, cover_size in networks:
        analysis["avg_nodes"] += G.number_of_nodes()
        analysis["avg_edges"] += G.number_of_edges()
        analysis["avg_cover_size"] += cover_size
        
        cover_ratio = cover_size / G.number_of_nodes()
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

def get_vertex_cover_problem(networks, idx=None):
    """
    Extract a vertex cover problem from the networks.
    
    Parameters:
    - networks: List of generated network tuples
    - idx: Optional index to select a specific network (random if None)
    
    Returns:
    - A tuple containing the graph and the vertex cover solution
    """
    if idx is None:
        idx = random.randint(0, len(networks) - 1)
    
    G, vertex_cover, cover_size = networks[idx]
    
    # Create a problem instance
    problem = {
        "graph": G,
        "vertex_cover": vertex_cover,
        "cover_size": cover_size
    }
    
    return problem

if __name__ == "__main__":
    networks = generate_networks(max_nodes=12, num_networks=300)
    print(f"Generated {len(networks)} graphs for the vertex cover problem")
    
    # Verify the networks
    verification = verify_vertex_covers(networks)
    print(f"Verification results: {verification}")
    
    # Analyze the networks
    analysis = analyze_networks(networks)
    print(f"Network analysis: {analysis}")
    
    # Save and visualize
    save_networks(networks, "algorithms/vertex_cover/vertex_cover_data.pkl")
    visualize_networks(networks, "algorithms/vertex_cover/figures")
    
    # Extract a sample vertex cover problem
    sample_problem = get_vertex_cover_problem(networks)
    print(f"Sample vertex cover problem: nodes={sample_problem['graph'].number_of_nodes()}, "
          f"edges={sample_problem['graph'].number_of_edges()}, "
          f"cover size={sample_problem['cover_size']}")