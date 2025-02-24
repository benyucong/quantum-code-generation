import json
import os
from typing import List

import concurrent

from networkx.readwrite import json_graph
from networkx import weisfeiler_lehman_graph_hash
from dimod import BinaryQuadraticModel
from src.algorithms.community_detection.community_detection import CommunityDetection
from src.algorithms.factory import get_problem_data
from src.algorithms.hypermaxcut.hypermaxcut import HyperMaxCut
from src.binary_optimization_problem import (
    BinaryOptimizationProblem,
)
from src.solver import (
    OptimizationProblemType,
    OptimizationType,
    AdaptiveProcess,
    CommunityDetectionAttributes,
    ExactSolution,
    OptimizationProblem,
    QuantumSolution,
)
from src.utils import DataclassJSONEncoder, int_to_bitstring

QUBIT_LIMIT = 17


class DataGenerator:
    def __init__(
        self,
        problem: OptimizationProblemType,
        output_path: str,
        ansatz_template: int,
        layers: int,
    ):
        self.problem = problem
        self.output_path = output_path
        self.ansatz_template = ansatz_template
        self.layers = layers

    def generate_data(self) -> None:
        """
        Retrieves graph data, converts it into binary optimization problems,
        and processes each using all available optimization types.
        """
        graph_data = get_problem_data(self.problem, generate_data=False)

        # Process the binary problems for each optimization type.
        for optimization_type in list(OptimizationType):
            self._process_problems(optimization_type, graph_data, self.ansatz_template)

    def _get_binary_polynomial(self, graph_data) -> BinaryQuadraticModel:
        """
        Converts graph data to a binary polynomial.
        """
        if self.problem == OptimizationProblemType.COMMUNITY_DETECTION:
            # Here, we assume graph_data is a tuple: (graph, n_communities, size_communities)
            graph, n_communities, size_communities = graph_data
            p = CommunityDetection(graph, n_communities)
            return p.get_binary_polynomial()
        else:
            raise ValueError("No binary polynomial defined for this problem type.")

    def _process_problem(
        self,
        graph_data: str,
        optimization_type: OptimizationType,
        ansatz_template: int,
        iteration_info: tuple,
    ) -> str:
        """
        Process a single binary optimization problem.
        """
        problem_specific_attributes = None

        binary_polynomial = None
        if self.problem == OptimizationProblemType.COMMUNITY_DETECTION:
            graph, n_communities, size_communities = graph_data
            binary_polynomial = CommunityDetection(graph, n_communities)
            problem_specific_attributes = CommunityDetectionAttributes(
                communities_size=size_communities, number_of_communities=n_communities
            )
        elif self.problem == OptimizationProblemType.HYPERMAXCUT:
            graph = graph_data
            binary_polynomial = HyperMaxCut(graph)
        else:
            raise ValueError("Invalid optimization problem.")

        problem = BinaryOptimizationProblem(
            binary_polynomial=binary_polynomial.get_binary_polynomial(), p=self.layers
        )

        n_qubits = problem.get_number_of_qubits()
        if n_qubits > QUBIT_LIMIT:
            return []

        smallest_eigenvalues, smallest_bitstrings, first_excited_energy = (
            problem.solve_exactly()
        )

        print(
            f"Processing {iteration_info[0] + 1}/{iteration_info[1]} for {n_qubits} qubits using {optimization_type}"
        )
        SOLUTION = {}
        if optimization_type == OptimizationType.VQE:
            SOLUTION = problem.solve_with_vqe(ansatz_template)
        elif optimization_type == OptimizationType.QAOA:
            SOLUTION = problem.solve_with_qaoa()
        elif optimization_type == OptimizationType.ADAPTIVE_VQE:
            SOLUTION = problem.solve_with_adaptive_vqe()
        else:
            raise ValueError("Invalid optimization type.")

        bitstrings = [
            int_to_bitstring(state, n_qubits)
            for state in SOLUTION.get("two_most_probable_states")
        ]
        circuit = None
        if (
            optimization_type == OptimizationType.VQE
            or optimization_type == OptimizationType.ADAPTIVE_VQE
        ):
            circuit = problem.vqe_circuit
        elif optimization_type == OptimizationType.QAOA:
            circuit = problem.qaoa_circuit

        params = (
            SOLUTION.get("params", None).tolist()
            if SOLUTION.get("params", None) is not None
            else None
        )
        solution = QuantumSolution(
            states=SOLUTION.get("states"),
            expectation_value=SOLUTION.get("expectation_value"),
            params=params,
            bitstrings=bitstrings,
            total_optimization_steps=SOLUTION.get("total_optimization_steps"),
            probabilities=SOLUTION.get("probabilities"),
        )

        problem_data = OptimizationProblem(
            problem_type=self.problem,
            optimization_type=optimization_type,
            signature=weisfeiler_lehman_graph_hash(graph),
            graph=json_graph.node_link_data(graph, edges="edges"),
            cost_hamiltonian=str(problem.get_cost_hamiltonian()),
            number_of_qubits=n_qubits,
            number_of_layers=self.layers,
            ansatz_id=ansatz_template,
            exact_solution=ExactSolution(
                smallest_eigenvalues=smallest_eigenvalues,
                number_of_smallest_eigenvalues=len(smallest_bitstrings),
                first_excited_energy=first_excited_energy,
                smallest_bitstrings=smallest_bitstrings,
            ),
            solution=solution,
            adaptive_process=AdaptiveProcess(
                circuits=problem.adaptive_circuits, gradients=problem.adaptive_gradients
            ),
            circuit_with_params=problem.circuit_to_qasm(
                circuit=circuit,
                params=params,
                symbolic_params=False,
                adapt_vqe=True
                if optimization_type == OptimizationType.ADAPTIVE_VQE
                else False,
            ),
            circuit_with_symbols=problem.circuit_to_qasm(
                circuit=circuit,
                params=None,
                symbolic_params=True,
                adapt_vqe=True
                if optimization_type == OptimizationType.ADAPTIVE_VQE
                else False,
            ),
            problem_specific_attributes=problem_specific_attributes,
        )

        return problem_data

    def _process_problems(
        self,
        optimization_type: OptimizationType,
        graph_data: List,
        ansatz_template: int,
    ) -> None:
        """
        Processes a list of binary optimization problems concurrently,
        and saves each solution.
        """
        print(
            f"Processing {optimization_type} problems... for {len(graph_data)} graphs"
        )
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._process_problem,
                    graph,
                    optimization_type,
                    ansatz_template,
                    (i, len(graph_data)),
                )
                for i, graph in enumerate(graph_data)
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    solutions = future.result()
                    for solution in solutions:
                        self._save_solution(solution)
                except Exception as exc:
                    print(f"Processing failed with exception: {exc}")

    def _save_solution(self, solution: OptimizationProblem):
        """
        Saves a single optimization problem solution to disk.
        The filename format is:
            {self.description}_{optimization_type}_{n_qubits}_{layers}_{signature}.json
        """
        filename = (
            f"{self.problem}_{solution.optimization_type}_"
            f"{solution.number_of_qubits}_{self.layers}_{solution.signature}.json"
        )

        unique_path = os.path.join(self.output_path, filename)

        with open(unique_path, "w", encoding="utf-8") as file:
            json.dump(solution, file, cls=DataclassJSONEncoder, indent=4)
