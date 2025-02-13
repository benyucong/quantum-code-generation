import random
from typing import Tuple, Set, List

from data_generation.data_generator import DataGenerator
from data_generation.hypermaxcut.hypergraph import HyperGraph
from data_generation.hypermaxcut.hypermaxcutsolver import HyperMaxCutSolver
from data_generator import OptimizationProblem, ExactSolution, QuantumSolution
import json
import os


class HyperMaxCutDataGenerator(DataGenerator):
    def __init__(self):
        super().__init__("hypermaxcut")
        self.node_range = (4, 10)

    def generate_data(self):
        # First, we generate the hypergraphs
        hypergraphs = self.__generate_hypergraphs()

        solutions = []
        for hypergraph in hypergraphs:
            solver = HyperMaxCutSolver(self.n_qubits, self.layers, hypergraph)

            exact_solution = solver.solve_exact()

            # Solve using VQE
            vqe_solution = solver.solve_vqe()
            vqe_optimization_problem = OptimizationProblem(
                hypergraph=hypergraph,
                exact_solution=ExactSolution(
                    smallest_eigenvalues=exact_solution["smallest_eigenvalues"],
                    number_of_smallest_eigenvalues=exact_solution[
                        "number_of_smallest_eigenvalues"
                    ],
                    first_excited_energy=exact_solution["first_excited_energy"],
                ),
                quantum_solution=QuantumSolution(
                    states=vqe_solution["states"],
                    expectation_value=vqe_solution["expectation_value"],
                    params=vqe_solution["params"],
                    bitstrings=vqe_solution["bitstrings"],
                    total_optimization_steps=vqe_solution["total_optimization_steps"],
                    probabilities=vqe_solution["probabilities"],
                ),
            )

            # Solve using QAOA
            qaoa_solution = solver.solve_qaoa()
            qaoa_optimization_problem = OptimizationProblem(
                hypergraph=hypergraph,
                exact_solution=ExactSolution(
                    smallest_eigenvalues=exact_solution["smallest_eigenvalues"],
                    number_of_smallest_eigenvalues=exact_solution[
                        "number_of_smallest_eigenvalues"
                    ],
                    first_excited_energy=exact_solution["first_excited_energy"],
                ),
                quantum_solution=QuantumSolution(
                    states=qaoa_solution["states"],
                    expectation_value=qaoa_solution["expectation_value"],
                    params=qaoa_solution["params"],
                    bitstrings=qaoa_solution["bitstrings"],
                    total_optimization_steps=qaoa_solution["total_optimization_steps"],
                    probabilities=qaoa_solution["probabilities"],
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
