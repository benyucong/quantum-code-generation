import glob
import itertools
import json
import multiprocessing
import os
import random
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import List

from networkx import weisfeiler_lehman_graph_hash
from networkx.readwrite import json_graph

from src.algorithms.community_detection.community_detection import CommunityDetection
from src.algorithms.connected_components.connected_component import (
    ConnectedComponentContainingNode,
)
from src.algorithms.factory import get_problem_data
from src.algorithms.graph_coloring.graph_coloring import GraphColoring
from src.algorithms.graph_isomorphism.graph_isomorphism import GraphIsomorphism
from src.algorithms.hamiltonian_path.hamiltonian_path import HamiltonianPath
from src.algorithms.hypermaxcut.hypermaxcut import HyperMaxCut
from src.algorithms.kcliques.kclique import KClique
from src.binary_optimization_problem import (
    BinaryOptimizationProblem,
)
from src.data_classes import (
    AdaptiveProcess,
    CommunityDetectionAttributes,
    ConnectedComponentAttributes,
    ExactSolution,
    GraphColoringAttributes,
    GraphIsomorphismAttributes,
    HamiltonianPathAttributes,
    KCliqueAttributes,
    OptimizationProblem,
    OptimizationProblemType,
    OptimizationType,
    QuantumSolution,
)
from src.utils import DataclassJSONEncoder, get_qasm_circuits, int_to_bitstring

import jax.numpy as jnp
import pennylane as qml

multiprocessing.set_start_method("spawn", force=True)
QUBIT_LIMIT = 16


def _get_device_type():
    """Determine if GPU is available through JAX"""
    try:
        import jax

        if len(jax.devices("gpu")) > 0:
            return "gpu"
    except:
        pass
    return "cpu"


def _worker_init():
    """Initialize JAX and PennyLane for each worker process"""
    import jax

    device_type = _get_device_type()

    if device_type == "gpu":
        jax.config.update("jax_default_device", jax.devices("gpu")[0])
    else:
        jax.config.update("jax_default_device", jax.devices("cpu")[0])

    jax.config.update("jax_enable_x64", True)


def _process_task(args):
    """Helper function to process a single task"""
    generator, task = args
    i, graph, optimization_type = task
    try:
        solution = generator._process_problem(
            graph,
            optimization_type,
            generator.ansatz_template,
            (i, 1),
        )
        if solution:
            generator._save_solution(solution)
        return True
    except Exception as exc:
        print(f"Processing failed with exception: {exc}")
        traceback.print_exc()
        return False


class DataGenerator:
    """
    A class for generating and processing optimization problem data.


    Attributes:
        problem (OptimizationProblemType): The type of optimization problem to process.
        output_path (str): Directory path where the generated data will be saved.
        ansatz_template (int): The template ID for the quantum circuit ansatz.
        layers (int): Number of layers in the quantum circuit.

    Methods:
        generate_data(): Main method to generate and process optimization problems.
        _process_problem(): Processes a single optimization problem instance.
        _solution_exists(): Checks if a solution already exists in the output directory.
        _process_problems(): Handles parallel processing of multiple optimization problems.
        _save_solution(): Saves processed solution to disk.

    Example:
        generator = DataGenerator(
            problem=OptimizationProblemType.COMMUNITY_DETECTION,
            output_path="./data",
            ansatz_template=1,
            layers=2
        generator.generate_data()
    """

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
        self.device_type = _get_device_type()
        print(f"Using device type: {self.device_type}")

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
            graph, graph_2 = graph_data
            binary_polynomial = GraphIsomorphism(graph, graph_2)
            problem_specific_attributes = GraphIsomorphismAttributes(
                autoisomorphic_graph=json_graph.node_link_data(graph_2, edges="edges")
            )
        elif self.problem == OptimizationProblemType.K_CLIQUE:
            graph, complete_graph, k = graph_data
            binary_polynomial = KClique(graph, k)
            problem_specific_attributes = KCliqueAttributes(k=k)
        elif self.problem == OptimizationProblemType.HAMILTONIAN_PATH:
            graph, hamiltonian_path, start_node, end_node = graph_data
            binary_polynomial = HamiltonianPath(
                graph, hamiltonian_path, start_node, end_node
            )
            problem_specific_attributes = HamiltonianPathAttributes(
                start_node=start_node, end_node=end_node
            )
        else:
            raise ValueError("Invalid optimization problem.")

        if graph is None:
            raise ValueError("Make sure graph is defined.")

        problem = BinaryOptimizationProblem(
            binary_polynomial=binary_polynomial.get_binary_polynomial(),
            description=self.problem,
            p=self.layers,
            device_type=self.device_type,
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
        start_time = time.time()
        if optimization_type == OptimizationType.VQE:
            solution = problem.solve_with_vqe(ansatz_template)
        elif optimization_type == OptimizationType.QAOA:
            solution = problem.solve_with_qaoa()
        elif optimization_type == OptimizationType.ADAPTIVE_VQE:
            solution = problem.solve_with_adaptive_vqe()
        else:
            raise ValueError("Invalid optimization type.")
        optimization_time = time.time() - start_time

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
            optimization_time=optimization_time,
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
        Processes optimization problems using either parallel (CPU) or sequential (GPU) execution.
        """
        print(f"Processing problems for {len(graph_data)} graphs")

        # Gather tasks and filter out existing solutions
        tasks = []
        for i, (graph, optimization_type) in enumerate(
            itertools.product(graph_data, list(OptimizationType))
        ):
            graph_for_signature = graph[0] if isinstance(graph, tuple) else graph
            n_qubits = len(graph_for_signature.nodes)

            signature = (
                hash(graph_for_signature)
                if self.problem == OptimizationProblemType.HYPERMAXCUT
                else weisfeiler_lehman_graph_hash(graph_for_signature)
            )

            if self._solution_exists(signature, optimization_type, n_qubits):
                print(
                    f"Skipping existing solution for signature {signature} with {optimization_type}"
                )
                continue

            tasks.append((i, graph, optimization_type))

        if not tasks:
            print("No tasks to process")
            return

        random.shuffle(tasks)
        # sort tasks by graph size (number of nodes) to start with easier problems
        tasks.sort(
            key=lambda task: len(
                task[1][0].nodes if isinstance(task[1], tuple) else task[1].nodes
            )
        )

        # ---------- GPU execution: process all tasks sequentially ----------
        if self.device_type == "gpu":
            print(f"Using GPU - processing {len(tasks)} tasks sequentially")
            _worker_init()
            for task in tasks:
                _process_task((self, task))
            return

        # ---------- CPU execution: process tasks in parallel ----------
        n_workers = max(1, int(multiprocessing.cpu_count() * 0.20))
        print(f"Using CPU - processing {len(tasks)} tasks with {n_workers} workers")

        # Separate tasks by optimization type
        tasks_vqe = [task for task in tasks if task[2] == OptimizationType.VQE]
        tasks_other = [task for task in tasks if task[2] != OptimizationType.VQE]

        # Process VQE tasks in parallel
        if False:
            print(f"Processing {len(tasks_vqe)} VQE tasks in parallel")
            with ProcessPoolExecutor(
                max_workers=n_workers, initializer=_worker_init
            ) as executor:
                args = [(self, task) for task in tasks_vqe]
                batch_size = max(1, len(args) // n_workers)
                for i in range(0, len(args), batch_size):
                    batch = args[i : i + batch_size]
                    list(executor.map(_process_task, batch))

        # Process non-VQE tasks sequentially
        if tasks_other:
            print(f"Processing {len(tasks_other)} non-VQE tasks sequentially")
            _worker_init()
            for task in tasks_other:
                _process_task((self, task))

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
