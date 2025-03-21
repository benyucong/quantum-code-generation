import pickle
import networkx as nx
import random
import matplotlib.pyplot as plt
from networkx import weisfeiler_lehman_graph_hash

random.seed(0)

def generate_flow_network(n_nodes: int, edge_density: float = 0.3, max_capacity: int = 20):
    """
    Generates a flow network with specified properties.
    
    Parameters:
    - n_nodes: Number of nodes in the graph.
    - network_type: Type of flow network ('single_source_sink', 'multi_source_sink', 'layered').
    - edge_density: Probability of adding an edge between two nodes.
    - max_capacity: Maximum capacity for any edge.
    
    Returns:
    - G: The generated directed graph with edge capacities.
    - source_nodes: List of source nodes.
    - sink_nodes: List of sink nodes.
    - max_flow_value: The maximum flow value (theoretical).
    """
    G = nx.DiGraph()
    nodes = list(range(n_nodes))
    G.add_nodes_from(nodes)
    
    # Single source (node 0) and single sink (node n-1)
    source_nodes = [0]
    sink_nodes = [n_nodes - 1]
    
    # Add edges with random capacities
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j and i not in sink_nodes and j not in source_nodes:
                if random.random() < edge_density:
                    capacity = random.randint(1, max_capacity)
                    G.add_edge(i, j, capacity=capacity)
    
    # Calculate the theoretical maximum flow
    # This is a simplification - actual max flow might be lower due to graph structure
    max_flow_value = calculate_max_flow(G, source_nodes[0], sink_nodes[0])
    
    return G, source_nodes[0], sink_nodes[0], max_flow_value

def calculate_max_flow(G, source, sink):
    """Calculate the maximum flow in the network."""
    return nx.maximum_flow_value(G, source, sink)

def generate_flow_with_cuts(G, source, sink):
    """
    Calculate the maximum flow and minimum cut in the network.
    
    Returns:
    - flow_dict: Dictionary of edge flows
    - cut_value: Value of the minimum cut
    - cut_edges: Edges in the minimum cut
    """
    flow_value, flow_dict = nx.maximum_flow(G, source, sink)
    
    # Find the minimum cut
    cut_value, partition = nx.minimum_cut(G, source, sink)
    reachable, non_reachable = partition
    
    # Find the edges in the cut
    cut_edges = []
    for u in reachable:
        for v in non_reachable:
            if G.has_edge(u, v):
                cut_edges.append((u, v))
    
    assert flow_value == cut_value, "Max flow does not equal min cut!"
    
    return flow_dict, cut_value, cut_edges

def generate_networks(max_nodes=10, num_networks=100):
    """
    Generate a collection of flow networks with different properties.
    
    Returns a list of tuples containing:
    - The graph
    - Source nodes
    - Sink nodes
    - Maximum flow value
    - Flow dictionary
    - Cut value
    - Cut edges
    - Network type
    """
    networks = []
    generated_networks = set()
    
    for n_nodes in range(2, max_nodes + 1, 1):
        for _ in range(num_networks):
            edge_density = random.uniform(0.2, 0.4)
            max_capacity = random.randint(2, 7)
            
            max_flow_value = 0
            i = 0
            while max_flow_value == 0 and i < 10:
                G, source, sink, max_flow_value = generate_flow_network(n_nodes, edge_density, max_capacity)
                i += 1
            
            if max_flow_value == 0:
                continue

            # Skip networks that are not connected
            if not nx.is_connected(G.to_undirected()):
                continue
            
            h = weisfeiler_lehman_graph_hash(G.to_undirected()) + f"_{source}_{sink}"
            
            if h in generated_networks:
                continue
            
            generated_networks.add(h)
            
            flow_dict, cut_value, cut_edges = generate_flow_with_cuts(G, source, sink)
            
            networks.append((
                G, source, sink, max_flow_value,
                flow_dict, cut_value, cut_edges
            ))
    
    return networks

def save_networks(networks, filename="max_flow_data.pkl"):
    """Save generated networks to a pickle file."""
    with open(filename, "wb") as f:
        pickle.dump(networks, f)

def visualize_networks(networks, output_dir="figures"):
    """Visualize a sample of the generated networks."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample some networks to visualize
    samples = random.sample(networks, min(30, len(networks)))
    
    for i, (G, source, sink, max_flow, flow_dict, cut_value, cut_edges) in enumerate(samples):
        plt.figure(figsize=(10, 8))
        
        pos = nx.spring_layout(G, seed=42)
        
        # Draw the edges with capacities
        edge_labels = {(u, v): f"{G[u][v]['capacity']}" for u, v in G.edges()}
        nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=700)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        # Highlight the source and sink nodes
        nx.draw_networkx_nodes(G, pos, nodelist=[source], node_color='green', node_size=800)
        nx.draw_networkx_nodes(G, pos, nodelist=[sink], node_color='red', node_size=800)
        
        # Highlight the cut edges
        flow_edges = [(u, v) for u in flow_dict for v in flow_dict[u] if flow_dict[u][v] > 0]
        nx.draw_networkx_edges(G, pos, edgelist=flow_edges, edge_color='red', width=2)
        
        title = f"Network\nNodes: {G.number_of_nodes()}, Max Flow: {cut_value}"
        plt.title(title)
        plt.savefig(f"{output_dir}/network_{i}.png")
        plt.close()

def verify_networks(networks):
    """Verify that generated networks satisfy max-flow min-cut theorem."""
    results = {"valid": 0, "invalid": 0}
    
    for G, source, sink, max_flow, flow_dict, cut_value, cut_edges in networks:
        
        # Check if flow value equals cut value
        if abs(max_flow - cut_value) < 1e-6:
            # Check if all cut edges are fully saturated
            cut_is_saturated = True
            for u, v in cut_edges:
                edge_flow = flow_dict[u][v]
                edge_capacity = G[u][v]['capacity']
                if abs(edge_flow - edge_capacity) > 1e-6:
                    cut_is_saturated = False
                    break
            
            if cut_is_saturated:
                results["valid"] += 1
            else:
                results["invalid"] += 1
        else:
            results["invalid"] += 1
    
    return results

def analyze_networks(networks):
    """Analyze the properties of the generated networks."""
    analysis = {
        "avg_nodes": 0,
        "avg_edges": 0,
        "avg_max_flow": 0,
        "min_max_flow": float('inf'),
        "max_max_flow": 0,
        "avg_cut_size": 0
    }
    
    for G, source, sink, max_flow, flow_dict, cut_value, cut_edges in networks:
        analysis["avg_nodes"] += G.number_of_nodes()
        analysis["avg_edges"] += G.number_of_edges()
        analysis["avg_max_flow"] += max_flow
        analysis["min_max_flow"] = min(analysis["min_max_flow"], max_flow)
        analysis["max_max_flow"] = max(analysis["max_max_flow"], max_flow)
        analysis["avg_cut_size"] += len(cut_edges)
    
    if networks:
        n = len(networks)
        analysis["avg_nodes"] /= n
        analysis["avg_edges"] /= n
        analysis["avg_max_flow"] /= n
        analysis["avg_cut_size"] /= n
    
    return analysis

if __name__ == "__main__":
    networks = generate_networks(max_nodes=6, num_networks=100000)
    print(f"Generated {len(networks)} flow networks with various properties")
    
    # Verify the networks
    verification = verify_networks(networks)
    print(f"Verification results: {verification}")
    
    # Analyze the networks
    analysis = analyze_networks(networks)
    print(f"Network analysis: {analysis}")
    
    # Save and visualize
    save_networks(networks, "algorithms/max_flow/max_flow_data.pkl")
    visualize_networks(networks, "algorithms/max_flow/figures")