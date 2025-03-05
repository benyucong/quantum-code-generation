import pickle
from src.algorithms.community_detection.community_detection_graphs import (
    generate_community_graphs,
)
from src.algorithms.hypermaxcut.hypermaxcut_graphs import (
    generate_hypergraphs,
)
from src.algorithms.connected_components.connected_component_graphs import (
    generate_graphs as generate_connected_components_graphs,
)
from src.algorithms.graph_coloring.graph_coloring_graphs import (
    generate_graphs as generate_graph_coloring_graphs,
)
from src.algorithms.graph_isomorphism.graph_isomorphism_graphs import (
    generate_graphs as generate_graph_isomorphism_graphs,
)
from src.algorithms.kcliques.kclique_graphs import (
    generate_kclique_data_set as generate_k_clique_graphs,
)
from src.solver import OptimizationProblemType


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
        return generate_k_clique_graphs()
    else:
        raise ValueError("No problem specified")


# def get_problem_polynomial(
#     problem: OptimizationProblemType, generate_data: bool = False
# ):
#     """Get the polynomial for the optimization problem.

#     Args:
#         problem (OptimizationProblem): The optimization problem.

#     Returns:
#         Polynomial: The polynomial for the optimization problem.
#     """
#     graph_data = get_problem_data(problem, generate_data)

#     if problem.problem_type == OptimizationProblemType.HYPERMAXCUT:
#         p = HyperMaxCut(graph_data)
#         return p.get_binary_polynomial()
#     elif problem.problem_type == OptimizationProblemType.COMMUNITY_DETECTION:
#         return CommunityDetection(graph_data)
#     else:
#         raise ValueError("No problem specified")
