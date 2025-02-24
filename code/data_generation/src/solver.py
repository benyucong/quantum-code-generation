from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


from .ansatz import Ansatz


class OptimizationProblemType(str, Enum):
    """
    Enum class representing different types of optimization problems.

    Attributes:
        HYPERGRAPH_CUT (str): Represents the hypergraph cut optimization problem type.
    """

    CONNECTED_COMPONENTS = "connected_components"
    COMMUNITY_DETECTION = "community_detection"
    K_CLIQUE = "kclique"
    HYPERMAXCUT = "hypermaxcut"
    GRAPH_ISOMORPHISM = "graph_isomorphism"
    GRAPH_COLORING = "graph_coloring"


class OptimizationType(str, Enum):
    """
    Enum class representing different types of optimization algorithms.

    Attributes:
        VQE (str): Variational Quantum Eigensolver.
        QAOA (str): Quantum Approximate Optimization Algorithm.
    """

    VQE = "vqe"
    ADAPTIVE_VQE = "adaptive_vqe"
    QAOA = "qaoa"


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


@dataclass
class AdaptiveProcess:
    circuits: List[str]
    gradients: List[float]


@dataclass
class CommunityDetectionAttributes:
    communities_size: int
    number_of_communities: int


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


class Solver(ABC):
    @abstractmethod
    def get_cost_hamiltonian(self):
        pass

    @abstractmethod
    def solve_exactly(self):
        pass

    @abstractmethod
    def solve_with_vqe(self, ansatz: Ansatz):
        pass

    @abstractmethod
    def solve_with_adaptive_vqe(self):
        pass

    @abstractmethod
    def solve_with_qaoa(self):
        pass

    @abstractmethod
    def circuit_to_qasm(self):
        pass

    @abstractmethod
    def get_number_of_qubits(self):
        pass

    @abstractmethod
    def get_number_of_layers(self):
        pass
