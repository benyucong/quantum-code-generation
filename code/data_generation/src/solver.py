from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


from .ansatz import Ansatz


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

    def circuit_to_qasm(self):
        pass

    @abstractmethod
    def get_number_of_qubits(self):
        pass

    @abstractmethod
    def get_number_of_layers(self):
        pass
