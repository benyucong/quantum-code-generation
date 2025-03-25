from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


class OptimizationProblemType(str, Enum):
    """
    Enum class representing different types of supported optimization problems.
    """

    CONNECTED_COMPONENTS = "connected_components"
    COMMUNITY_DETECTION = "community_detection"
    K_CLIQUE = "kclique"
    HYPERMAXCUT = "hypermaxcut"
    GRAPH_ISOMORPHISM = "graph_isomorphism"
    GRAPH_COLORING = "graph_coloring"
    HAMILTONIAN_PATH = "hamiltonian_path"
    MATCHING = "matching"
    MAX_FLOW = "max_flow"
    MIN_CUT = "min_cut"
    STEINER_TREE = "steiner_tree"


class OptimizationType(str, Enum):
    """
    Enum class representing different types of supported optimization algorithms.
    """

    VQE = "vqe"
    ADAPTIVE_VQE = "adaptive_vqe"
    QAOA = "qaoa"


class MatchingType(str, Enum):
    """
    Enum class representing different types of supported matching types.
    """

    PERFECT = "perfect"
    NEAR_PERFECT = "near_perfect"
    MAXIMUM = "maximum"


@dataclass
class ExactSolution:
    smallest_eigenvalues: float
    number_of_smallest_eigenvalues: int
    first_excited_energy: float
    smallest_bitstrings: Optional[List[str]]


@dataclass
class QuantumSolution:
    states: List[int]
    expectation_value: float
    params: List[Any]
    bitstrings: List[str]
    total_optimization_steps: int
    probabilities: List[float]
    optimization_time: float


@dataclass
class AdaptiveProcess:
    circuits: List[str]
    gradients: List[float]


@dataclass
class CommunityDetectionAttributes:
    communities_size: int
    number_of_communities: int


@dataclass
class ConnectedComponentAttributes:
    node: str


@dataclass
class GraphColoringAttributes:
    number_of_colors: int


@dataclass
class GraphIsomorphismAttributes:
    autoisomorphic_graph: str


@dataclass
class KCliqueAttributes:
    k: int


@dataclass
class HamiltonianPathAttributes:
    start_node: int
    end_node: int


@dataclass
class MatchingAttributes:
    matching: str
    extra: str


@dataclass
class MaxFlowAttributes:
    source: int
    sink: int


@dataclass
class MinCutAttributes:
    source: int
    sink: int


@dataclass
class SteinerTreeAttributes:
    terminal_nodes: List[int]


@dataclass
class OptimizationProblem:
    problem_type: OptimizationProblemType
    optimization_type: OptimizationType
    signature: str
    graph: str
    cost_hamiltonian: str
    number_of_qubits: int
    number_of_layers: int
    ansatz_id: Optional[int]
    exact_solution: ExactSolution
    solution: QuantumSolution
    adaptive_process: Optional[AdaptiveProcess]
    circuit_with_params: Optional[str]
    circuit_with_symbols: Optional[str]
    problem_specific_attributes: Optional[CommunityDetectionAttributes]
