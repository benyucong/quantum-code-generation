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
    
    for n_nodes in range(3, max_nodes + 1, 1):
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

def visualize_min_cuts(networks, output_dir="min_cut_figures"):
    """
    Visualize the minimum cuts for the generated networks.
    
    Parameters:
    - networks: List of generated network tuples
    - output_dir: Directory to save the output figures
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample some networks to visualize
    samples = random.sample(networks, min(30, len(networks)))
    
    for i, (G, source, sink, max_flow, flow_dict, cut_value, cut_edges) in enumerate(samples):
        plt.figure(figsize=(10, 8))
        
        # Use Graphviz layout for better visualization of cuts
        pos = nx.spring_layout(G) #nx.nx_agraph.graphviz_layout(G, prog='dot') if nx.nx_agraph.graphviz_layout else nx.spring_layout(G, seed=42)
        
        # Find the partition (S, T) defined by the min-cut
        # S contains the source, T contains the sink
        S = set()
        T = set()
        
        # Create a residual graph
        residual = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            capacity = data['capacity']
            flow = flow_dict[u][v]
            residual_capacity = capacity - flow
            if residual_capacity > 0:
                residual.add_edge(u, v, capacity=residual_capacity)
            if flow > 0:
                residual.add_edge(v, u, capacity=flow)
        
        # Find nodes reachable from source in residual graph
        reachable = set(nx.descendants(residual, source))
        reachable.add(source)
        
        S = reachable
        T = set(G.nodes()) - S
        
        # Draw the graph
        # Nodes in S (source side)
        nx.draw_networkx_nodes(G, pos, nodelist=list(S), node_color='lightgreen', node_size=700)
        # Nodes in T (sink side)
        nx.draw_networkx_nodes(G, pos, nodelist=list(T), node_color='lightblue', node_size=700)
        # Node labels
        nx.draw_networkx_labels(G, pos)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', width=1)
        
        # Highlight source and sink
        nx.draw_networkx_nodes(G, pos, nodelist=[source], node_color='green', node_size=800)
        nx.draw_networkx_nodes(G, pos, nodelist=[sink], node_color='red', node_size=800)
        
        # Highlight the cut edges
        nx.draw_networkx_edges(G, pos, edgelist=cut_edges, edge_color='red', width=3)
        
        # Edge labels showing capacity and flow
        edge_labels = {(u, v): f"{flow_dict[u][v]}/{G[u][v]['capacity']}" for u, v in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        
        title = f"Min-Cut Visualization\nCut Value: {cut_value}, |S|: {len(S)}, |T|: {len(T)}"
        plt.title(title)
        plt.savefig(f"{output_dir}/min_cut_{i}.png")
        plt.close()

def analyze_min_cuts(networks):
    """
    Analyze the minimum cuts in the generated networks.
    
    Returns:
    - Dictionary of min-cut statistics
    """
    analysis = {
        "avg_cut_value": 0,
        "min_cut_value": float('inf'),
        "max_cut_value": 0,
        "avg_cut_size": 0,
        "avg_source_partition_size": 0,
        "avg_sink_partition_size": 0,
        "cut_to_edges_ratio": 0
    }
    
    for G, source, sink, max_flow, flow_dict, cut_value, cut_edges in networks:
        analysis["avg_cut_value"] += cut_value
        analysis["min_cut_value"] = min(analysis["min_cut_value"], cut_value)
        analysis["max_cut_value"] = max(analysis["max_cut_value"], cut_value)
        analysis["avg_cut_size"] += len(cut_edges)
        
        # Create a residual graph
        residual = nx.DiGraph()
        for u, v, data in G.edges(data=True):
            capacity = data['capacity']
            flow = flow_dict[u][v]
            residual_capacity = capacity - flow
            if residual_capacity > 0:
                residual.add_edge(u, v, capacity=residual_capacity)
            if flow > 0:
                residual.add_edge(v, u, capacity=flow)
        
        # Find nodes reachable from source in residual graph
        reachable = set()
        try:
            reachable = set(nx.descendants(residual, source))
            reachable.add(source)
        except nx.NetworkXError:
            # Handle the case when the source is isolated
            reachable = {source}
        
        source_partition = reachable
        sink_partition = set(G.nodes()) - source_partition
        
        analysis["avg_source_partition_size"] += len(source_partition)
        analysis["avg_sink_partition_size"] += len(sink_partition)
        
        if G.number_of_edges() > 0:
            analysis["cut_to_edges_ratio"] += len(cut_edges) / G.number_of_edges()
    
    if networks:
        n = len(networks)
        analysis["avg_cut_value"] /= n
        analysis["avg_cut_size"] /= n
        analysis["avg_source_partition_size"] /= n
        analysis["avg_sink_partition_size"] /= n
        analysis["cut_to_edges_ratio"] /= n
    
    return analysis

def get_min_cut_problem(networks, idx=None):
    """
    Extract a min-cut problem from the networks.
    
    Parameters:
    - networks: List of generated network tuples
    - idx: Optional index to select a specific network (random if None)
    
    Returns:
    - A tuple containing the graph, source, sink, capacities, and the min-cut solution
    """
    if idx is None:
        idx = random.randint(0, len(networks) - 1)
    
    G, source, sink, max_flow, flow_dict, cut_value, cut_edges = networks[idx]
    
    # Create a problem instance
    problem = {
        "graph": G,
        "source": source,
        "sink": sink,
        "capacities": {(u, v): data['capacity'] for u, v, data in G.edges(data=True)},
        "min_cut_value": cut_value,
        "min_cut_edges": cut_edges
    }
    
    return problem

# Update the main function to include min-cut specific analysis
if __name__ == "__main__":
    networks = generate_networks(max_nodes=13, num_networks=3000)
    print(f"Generated {len(networks)} flow networks with various properties")
    
    # Verify the networks
    verification = verify_networks(networks)
    print(f"Verification results: {verification}")
    
    # Analyze the networks
    flow_analysis = analyze_networks(networks)
    print(f"Network analysis: {flow_analysis}")
    
    # Min-cut specific analysis
    cut_analysis = analyze_min_cuts(networks)
    print(f"Min-cut analysis: {cut_analysis}")
    
    # Save and visualize
    save_networks(networks, "algorithms/min_cut/min_cut_data.pkl")
    
    # Visualize min-cuts specifically
    visualize_min_cuts(networks, "algorithms/min_cut/figures")
    
    # Extract a sample min-cut problem
    sample_problem = get_min_cut_problem(networks)
    print(f"Sample min-cut problem: source={sample_problem['source']}, sink={sample_problem['sink']}, "
          f"min-cut value={sample_problem['min_cut_value']}, cut size={len(sample_problem['min_cut_edges'])}")