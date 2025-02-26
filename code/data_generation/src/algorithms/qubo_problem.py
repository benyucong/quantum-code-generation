from abc import ABC, abstractmethod

from dimod import BinaryQuadraticModel


class QuadradicUnconstrainedBinaryOptimization(ABC):
    """
    Abstract base class for Quadratic Unconstrained Binary Optimization (QUBO) problems.

    This class defines the interface for QUBO problems, which are a type of optimization problem
    where the objective is to minimize a quadratic polynomial over binary variables.

    Methods
    -------
    get_binary_polynomial() -> BinaryQuadraticModel
        Abstract method to be implemented by subclasses. Should return the binary quadratic model
        representing the QUBO problem.
    """

    def __init__(self, description: str):
        self.description = description

    @abstractmethod
    def get_binary_polynomial(self) -> BinaryQuadraticModel:
        """
        Generate a binary polynomial representation of the current problem as a BinaryQuadraticModel.


        Returns:
            BinaryQuadraticModel: An instance of BinaryQuadraticModel representing the binary polynomial form
            of the problem.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
