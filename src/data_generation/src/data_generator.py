from abc import ABC, abstractmethod
import dataclasses
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

from pennylane import numpy as np
from pennylane.ops.op_math import LinearCombination


class OptimizationProblemType(str, Enum):
    """
    Enum class representing different types of optimization problems.

    Attributes:
        HYPERGRAPH_CUT (str): Represents the hypergraph cut optimization problem type.
    """

    HYPERGRAPH_CUT = "hypergraph_cut"


class OptimizationType(str, Enum):
    """
    Enum class representing different types of optimization algorithms.

    Attributes:
        VQE (str): Variational Quantum Eigensolver.
        QAOA (str): Quantum Approximate Optimization Algorithm.
    """

    VQE = "vqe"
    QAOA = "qaoa"


@dataclass
class ExactSolution:
    smallest_eigenvalues: float
    number_of_smallest_eigenvalues: int
    first_excited_energy: float


@dataclass
class QuantumSolution:
    states: List[int]
    expectation_value: float
    params: List[Any]
    bitstrings: List[str]
    total_optimization_steps: int
    probabilities: List[float]


@dataclass
class OptimizationProblem:
    problem_type: OptimizationProblemType
    optimization_type: OptimizationType
    signature: str
    cost_hamiltonian: str
    number_of_qubits: int
    number_of_layers: int
    ansatz_id: int = None
    exact_solution: ExactSolution = None
    qaoa_solution: QuantumSolution = None
    vqe_solution: QuantumSolution = None
    circuit_with_params: str = None
    circuit_with_symbols: str = None


class DataclassJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for encoding dataclass objects, numpy arrays, and LinearCombination objects.

    This encoder extends the default `json.JSONEncoder` to handle additional types:
    - Dataclass objects are converted to dictionaries using `dataclasses.asdict`.
    - Numpy arrays are converted to lists using `tolist`.
    - LinearCombination objects are converted to strings using `str`.

    Methods:
        default(obj): Overrides the default method to provide custom serialization for specific types.
    """

    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, LinearCombination):
            return str(obj)
        return super().default(obj)


class DataGenerator(ABC):
    def __init__(self, description=None):
        self.description = description

    @abstractmethod
    def generate_data(self):
        """
        Generates data for the application.

        This method is a placeholder and currently does not implement any functionality.
        Future implementations should include the logic for data generation.

        Returns:
            None
        """
