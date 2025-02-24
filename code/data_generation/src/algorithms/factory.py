import pickle
from src.algorithms.community_detection.community_detection import CommunityDetection
from src.algorithms.community_detection.community_detection_graphs import (
    generate_community_graphs,
)
from src.algorithms.hypermaxcut.hypermaxcut import HyperMaxCut
from src.algorithms.hypermaxcut.hypermaxcut_graphs import generate_hypergraphs
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
        return f"{problem}/{problem}_data.pkl"

    if problem == OptimizationProblemType.HYPERMAXCUT:
        return generate_hypergraphs()
    elif problem == OptimizationProblemType.COMMUNITY_DETECTION:
        return generate_community_graphs()
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
