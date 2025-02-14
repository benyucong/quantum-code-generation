import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Any
from pennylane import numpy as np
import json


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
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class DataGenerator:
    def __init__(self, description=None):
        self.description = description
        self.n_qubits = None
        self.layers = None

    def initialize(self, n_qubits: int, layers: int, output_path: str):
        self.n_qubits = n_qubits
        self.layers = layers
        self.output_path = output_path

    def generate_data(self):
        pass
