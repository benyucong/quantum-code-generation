from dataclasses import dataclass
import random
from typing import Tuple, Set, List

from ..data_generator import (
    DataGenerator,
    OptimizationProblem,
    ExactSolution,
    QuantumSolution,
)
from ..ansatz import AnsatzCircuit6
from .hypergraph import HyperGraph
from .hypermaxcut_solver import HyperMaxCutSolver
import json
import os


@dataclass
class HyperMaxCutOptimizationProblem(OptimizationProblem):
    hypergraph: HyperGraph = None


class HyperMaxCutDataGenerator(DataGenerator):
    def __init__(self):
        super().__init__("hypermaxcut")
        self.node_range = (4, 10)

    def generate_data(self):
        # First, we generate the hypergraphs
        hypergraphs = self.__generate_hypergraphs()

        ansatz = AnsatzCircuit6(num_qubits=self.n_qubits, layers=self.layers)

        solutions = []
        for hypergraph in hypergraphs:
            solver = HyperMaxCutSolver(self.n_qubits, self.layers, hypergraph)

            (
                smallest_eigenvalues,
                smallest_eigenvectors,
                smallest_bitstrings,
                first_excited_energy,
                first_excited_state,
            ) = solver.solve_exact()

            exact_solution = ExactSolution(
                smallest_eigenvalues=float(smallest_eigenvalues[0]),
                number_of_smallest_eigenvalues=len(smallest_eigenvalues),
                first_excited_energy=float(first_excited_energy),
            )

            # Solve using VQE
            (
                vqe_states,
                vqe_expectation_value,
                vqe_params,
                vqe_total_steps,
                vqe_probs,
            ) = solver.solve_vqe(ansatz=ansatz)
            # Solve using QAOA
            (
                qaoa_states,
                qaoa_expectation_value,
                qaoa_params,
                qaoa_total_steps,
                qaoa_probs,
            ) = solver.solve_qaoa()

            vqe_optimization_problem = HyperMaxCutOptimizationProblem(
                hypergraph=hypergraph,
                number_of_layers=self.layers,
                number_of_qubits=self.n_qubits,
                cost_hamiltonian=solver.get_cost_hamiltonian(),
                exact_solution=exact_solution,
                vqe_solution=QuantumSolution(
                    states=vqe_states,
                    expectation_value=vqe_expectation_value,
                    params=vqe_params,
                    bitstrings=smallest_bitstrings,
                    total_optimization_steps=vqe_total_steps,
                    probabilities=vqe_probs,
                ),
            )

            qaoa_optimization_problem = HyperMaxCutOptimizationProblem(
                hypergraph=hypergraph,
                number_of_layers=self.layers,
                number_of_qubits=self.n_qubits,
                cost_hamiltonian=solver.get_cost_hamiltonian(),
                exact_solution=exact_solution,
                qaoa_solution=QuantumSolution(
                    states=qaoa_states,
                    expectation_value=qaoa_expectation_value,
                    params=qaoa_params,
                    bitstrings=smallest_bitstrings,
                    total_optimization_steps=qaoa_total_steps,
                    probabilities=qaoa_probs,
                ),
            )

            solutions.append(vqe_optimization_problem)
            solutions.append(qaoa_optimization_problem)

        self._save_data(solutions)

    def __generate_hypergraphs(self) -> Set[HyperGraph]:
        hypergraphs: Set[HyperGraph] = set()

        for n_nodes in range(self.node_range[1], self.node_range[1] + 1):
            # The maximum amount of hyperedges
            max_hyperedges = n_nodes * (n_nodes - 1) // 2

            for n_hyperedges in range(1, max_hyperedges):
                for max_edge_size in range(2, n_nodes):
                    hypergraph = self.__generate_random_hypergraph(
                        n_nodes, n_hyperedges, max_edge_size
                    )
                    hypergraphs.add(hypergraph)
        return hypergraphs

    def __generate_random_hypergraph(
        self, num_nodes: int, num_hyperedges: int, max_edge_size: int
    ) -> HyperGraph:
        nodes = list(range(num_nodes))
        hyperedges = []

        for _ in range(num_hyperedges):
            edge_size = random.randint(2, max_edge_size)
            hyperedge = set(random.sample(nodes, edge_size))
            # Check that the hyperedge is not a subset of any other hyperedge
            if not any(
                hyperedge.issubset(h) or h.issubset(hyperedge) for h in hyperedges
            ):
                hyperedges.append(hyperedge)

        # Verify that every node is in at least one hyperedge
        for node in nodes:
            if not any(node in h for h in hyperedges):
                node2 = random.choice([n for n in nodes if n != node])
                hyperedge = set([node, node2])
                hyperedges.append(hyperedge)

        return HyperGraph(nodes, hyperedges)

    def _save_data(self, solutions: List[OptimizationProblem]):
        for i, solution in enumerate(solutions):
            unique_path = os.path.join(
                self.output_path,
                f"{self.description}_{self.n_qubits}_{self.layers}_{i}.json",
            )
            with open(unique_path, "w", encoding="utf-8") as file:
                json.dump(solution, file, indent=4)
