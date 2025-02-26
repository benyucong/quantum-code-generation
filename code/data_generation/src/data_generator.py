import glob
import itertools
import json
import os
import traceback
from typing import List

from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph

from src.algorithms.community_detection.community_detection import CommunityDetection
from src.algorithms.connected_components.connected_component import (
    ConnectedComponentContainingNode,
)
from src.algorithms.factory import get_problem_data
from src.algorithms.graph_coloring.graph_coloring import GraphColoring
from src.algorithms.hypermaxcut.hypermaxcut import HyperMaxCut
from src.algorithms.kcliques.kclique import KClique
from src.binary_optimization_problem import (
    BinaryOptimizationProblem,
)
from src.solver import (
    AdaptiveProcess,
    CommunityDetectionAttributes,
    ConnectedComponentAttributes,
    ExactSolution,
    GraphColoringAttributes,
    GraphIsomorphismAttributes,
    KCliqueAttributes,
    OptimizationProblem,
    OptimizationProblemType,
    OptimizationType,
    QuantumSolution,
)
from src.utils import DataclassJSONEncoder, get_qasm_circuits, int_to_bitstring

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
        graph_data = get_problem_data(self.problem, generate_data=True)

        # Process the binary problems for each optimization type.
        self._process_problems(graph_data, self.ansatz_template)

    def _process_problem(
        self,
        graph_data: str,
        optimization_type: OptimizationType,
        ansatz_template: int,
        iteration_info: tuple,
    ) -> OptimizationProblem:
        """
        Process a single binary optimization problem.
        """

        binary_polynomial = None
        problem_specific_attributes = None
        # --------- Parse the graph data and construct problem ---------
        # The graph data is different for each optimization problem.
        # Also build the probelem specific attributes for each problem.
        if self.problem == OptimizationProblemType.COMMUNITY_DETECTION:
            graph, n_communities, size_communities = graph_data
            binary_polynomial = CommunityDetection(graph, n_communities)
            problem_specific_attributes = CommunityDetectionAttributes(
                communities_size=size_communities, number_of_communities=n_communities
            )
        elif self.problem == OptimizationProblemType.HYPERMAXCUT:
            # If the problem is HyperMaxCut, graph_data is a hypergraph
            graph = graph_data
            binary_polynomial = HyperMaxCut(graph)
        elif self.problem == OptimizationProblemType.CONNECTED_COMPONENTS:
            graph, node, components = graph_data
            binary_polynomial = ConnectedComponentContainingNode(graph, node)
            problem_specific_attributes = ConnectedComponentAttributes(node=node)
        elif self.problem == OptimizationProblemType.GRAPH_COLORING:
            graph, n_colors, coloring = graph_data
            binary_polynomial = GraphColoring(graph, n_colors)
            problem_specific_attributes = GraphColoringAttributes(
                number_of_colors=n_colors
            )
        elif self.problem == OptimizationProblemType.GRAPH_ISOMORPHISM:
            graph, n_colors, coloring = graph_data
            binary_polynomial = GraphColoring(graph, n_colors)
            problem_specific_attributes = GraphIsomorphismAttributes(
                number_of_colors=n_colors
            )
        elif self.problem == OptimizationProblemType.K_CLIQUE:
            graph, complete_graph, k = graph_data
            binary_polynomial = KClique(graph, k)
            problem_specific_attributes = KCliqueAttributes(k=k)
        else:
            raise ValueError("Invalid optimization problem.")

        problem = BinaryOptimizationProblem(
            binary_polynomial=binary_polynomial.get_binary_polynomial(), p=self.layers
        )

        # --------- Solve the problem using the specified optimization type ---------
        n_qubits = problem.get_number_of_qubits()
        if n_qubits > QUBIT_LIMIT:
            return []

        (
            smallest_eigenvalues,
            smallest_bitstrings,
            first_excited_energy,
            smallest_eigenvectors,
        ) = problem.solve_exactly()

        print(
            f"Processing {iteration_info[0] + 1}/{iteration_info[1]} for {n_qubits} qubits using {optimization_type}"
        )

        solution = {}
        if optimization_type == OptimizationType.VQE:
            solution = problem.solve_with_vqe(ansatz_template)
        elif optimization_type == OptimizationType.QAOA:
            solution = problem.solve_with_qaoa()
        elif optimization_type == OptimizationType.ADAPTIVE_VQE:
            solution = problem.solve_with_adaptive_vqe()
        else:
            raise ValueError("Invalid optimization type.")

        # Check if a solution was found.
        if not solution.get("success"):
            print("No solution found for problem.")
            return []

        bitstrings = [
            int_to_bitstring(state, n_qubits)
            for state in solution.get("two_most_probable_states", [])
        ]
        params = solution.get("params", None)

        circuit = None
        if optimization_type == OptimizationType.VQE:
            circuit = problem.vqe_circuit
        elif optimization_type == OptimizationType.ADAPTIVE_VQE:
            circuit = problem.adaptive_vqe_circuit
        elif optimization_type == OptimizationType.QAOA:
            circuit = problem.qaoa_circuit

        q_solution = QuantumSolution(
            states=solution.get("two_most_probable_states"),
            expectation_value=solution.get("expectation_value"),
            params=params,
            bitstrings=bitstrings,
            total_optimization_steps=solution.get("total_steps"),
            probabilities=solution.get("states_probs"),
        )

        circuit_with_params, circuit_with_symbols = get_qasm_circuits(
            problem, optimization_type, params
        )

        problem_data = OptimizationProblem(
            problem_type=self.problem,
            optimization_type=optimization_type,
            signature=weisfeiler_lehman_graph_hash(graph)
            if self.problem != OptimizationProblemType.HYPERMAXCUT
            else hash(graph),
            graph=json_graph.node_link_data(graph, edges="edges")
            if self.problem != OptimizationProblemType.HYPERMAXCUT
            else graph.__dict__(),
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
            solution=q_solution,
            adaptive_process=AdaptiveProcess(
                circuits=problem.adaptive_circuits, gradients=problem.adaptive_gradients
            ),
            circuit_with_params=circuit_with_params,
            circuit_with_symbols=circuit_with_symbols,
            problem_specific_attributes=problem_specific_attributes,
        )

        return problem_data

    def _solution_exists(
        self, signature: str, optimization_type: OptimizationType, n_qubits: int
    ) -> bool:
        """
        Check if a solution with the given signature already exists in the output directory.
        """
        pattern = os.path.join(
            self.output_path,
            f"{self.problem}_{optimization_type}_{n_qubits}_{self.layers}_{signature}.json",
        )
        return bool(glob.glob(pattern))

    def _process_problems(
        self,
        graph_data: List,
        ansatz_template: int,
    ) -> None:
        """
        Processes optimization problems sequentially to avoid JAX multithreading issues.
        """
        print(f"Processing problems for {len(graph_data)} graphs")

        # --------- Filter out existing solutions ---------
        tasks = []
        for i, (graph, optimization_type) in enumerate(
            itertools.product(graph_data, list(OptimizationType))
        ):
            # Get the signature for the current graph
            if self.problem != OptimizationProblemType.HYPERMAXCUT:
                signature = weisfeiler_lehman_graph_hash(
                    graph[0] if isinstance(graph, tuple) else graph
                )
            else:
                signature = hash(graph)

            n_qubits = (
                len(graph[0].nodes()) if isinstance(graph, tuple) else len(graph.nodes)
            )

            # Skip if solution already exists
            if self._solution_exists(signature, optimization_type, n_qubits):
                print(
                    f"Skipping existing solution for signature {signature} with {optimization_type}"
                )
                continue

            tasks.append((i, graph, optimization_type))

        # --------- Process the remaining problems ---------
        for i, graph, optimization_type in tasks:
            try:
                solution = self._process_problem(
                    graph,
                    optimization_type,
                    ansatz_template,
                    (i, len(tasks)),
                )
                if solution:
                    self._save_solution(solution)
            except Exception as exc:
                print(f"Processing failed with exception: {exc}")
                traceback.print_exc()

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
        print(f"Saving solution to {filename}")
        unique_path = os.path.join(self.output_path, filename)

        with open(unique_path, "w", encoding="utf-8") as file:
            json.dump(solution, file, cls=DataclassJSONEncoder, indent=4)
