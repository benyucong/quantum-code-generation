import pickle

from src.algorithms.community_detection.community_detection_graphs import (
    generate_community_graphs,
)
from src.algorithms.connected_components.connected_component_graphs import (
    generate_graphs as generate_connected_components_graphs,
)
from src.algorithms.edge_cover.edge_cover_graphs import (
    generate_networks as generate_edge_cover_graphs,
)
from src.algorithms.graph_coloring.graph_coloring_graphs import (
    generate_graphs as generate_graph_coloring_graphs,
)
from src.algorithms.graph_isomorphism.graph_isomorphism_graphs import (
    generate_graphs as generate_graph_isomorphism_graphs,
)
from src.algorithms.hamiltonian_path.hamiltonian_path_graphs import (
    generate_graphs as generate_hamiltonian_path_graphs,
)
from src.algorithms.hypermaxcut.hypermaxcut_graphs import (
    generate_hypergraphs,
)
from src.algorithms.kcliques.kclique_graphs import (
    generate_kclique_data_set as generate_k_clique_graphs,
)
from src.algorithms.matching.matching_graphs import (
    generate_graphs as generate_matching_graphs,
)
from src.algorithms.max_flow.max_flow_graphs import (
    generate_networks as generate_max_flow_graphs,
)
from src.algorithms.min_cut.min_cut_graphs import (
    generate_networks as generate_min_cut_graphs,
)
from src.algorithms.steiner_tree.steiner_tree_graphs import (
    generate_steiner_dataset as generate_steiner_tree_graphs,
)
from src.algorithms.vertex_cover.vertex_cover_graphs import (
    generate_networks as generate_vertex_cover_graphs,
)
from src.data_classes import OptimizationProblemType


def load_pickle(filename):
    with open(filename, "rb") as f:
        graphs = pickle.load(f)
    return graphs


def get_problem_data(problem: OptimizationProblemType, generate_data: bool = False):
    """Get the data for the optimization problem.

    Args:
        problem (OptimizationProblem): The optimization problem.

    Returns:
        DataGenerator: The data generator for the optimization problem.
    """
    if not generate_data:
        return load_pickle(f"src/algorithms/{problem}/{problem}_data.pkl")

    print("Generating data for problem: ", problem)

    if problem == OptimizationProblemType.HYPERMAXCUT:
        min_num_nodes, max_num_nodes = 3, 14
        hypergraphs = generate_hypergraphs(min_num_nodes, max_num_nodes)
        return hypergraphs
    elif problem == OptimizationProblemType.COMMUNITY_DETECTION:
        max_n_cliques, max_size = 5, 5
        return generate_community_graphs(max_n_cliques, max_size)
    elif problem == OptimizationProblemType.CONNECTED_COMPONENTS:
        max_nodes, min_components, max_components, iterations = 16, 2, 8, 100
        return generate_connected_components_graphs(
            max_nodes, min_components, max_components, iterations
        )
    elif problem == OptimizationProblemType.GRAPH_COLORING:
        max_colors = 6
        max_nodes = 16
        return generate_graph_coloring_graphs(max_colors, max_nodes)
    elif problem == OptimizationProblemType.GRAPH_ISOMORPHISM:
        max_nodes = 10
        return generate_graph_isomorphism_graphs(max_nodes)
    elif problem == OptimizationProblemType.K_CLIQUE:
        max_k = 5
        return generate_k_clique_graphs(5)
    elif problem == OptimizationProblemType.HAMILTONIAN_PATH:
        max_nodes = 10
        return generate_hamiltonian_path_graphs(max_nodes=max_nodes)
    elif problem == OptimizationProblemType.MATCHING:
        max_nodes = 10
        return generate_matching_graphs(max_nodes=max_nodes)
    elif problem == OptimizationProblemType.MAX_FLOW:
        max_nodes = 12
        return generate_max_flow_graphs(max_nodes=max_nodes)
    elif problem == OptimizationProblemType.MIN_CUT:
        max_nodes = 12
        return generate_min_cut_graphs(max_nodes=max_nodes)
    elif problem == OptimizationProblemType.STEINER_TREE:
        n_instances = 100
        return generate_steiner_tree_graphs(n_instances=n_instances)
    elif problem == OptimizationProblemType.VERTEX_COVER:
        max_nodes = 12
        return generate_vertex_cover_graphs(max_nodes=max_nodes)
    elif problem == OptimizationProblemType.EDGE_COVER:
        max_nodes = 12
        return generate_edge_cover_graphs(max_nodes=max_nodes)
    else:
        raise ValueError("No graph generator for this problem.")
