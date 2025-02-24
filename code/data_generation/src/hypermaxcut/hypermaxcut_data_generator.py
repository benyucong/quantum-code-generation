import concurrent.futures
import json
import os
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Set

from pennylane import numpy as np
from src.ansatz import get_ansatz
from src.data_generator import (
    DataclassJSONEncoder,
    DataGenerator,
    ExactSolution,
    OptimizationProblem,
    OptimizationProblemType,
    OptimizationType,
    QuantumSolution,
)
from src.hypermaxcut.hypergraph import HyperGraph
from src.hypermaxcut.hypermaxcut_solver import HyperMaxCutSolver


def int_to_bitstring(int_sample: int, n_qubits: int) -> str:
    """
    Converts an integer to a bitstring of a specified length.

    Args:
        int_sample (int): The integer to be converted to a bitstring.
        n_qubits (int): The length of the resulting bitstring.

    Returns:
        str: The bitstring representation of the integer, padded with leading zeros to match the specified length.
    """
    bits = np.array([int(i) for i in format(int_sample, f"0{n_qubits}b")])
    return "".join([str(i) for i in bits])


# --- Helper function to process one hypergraph ---
def process_hypergraph(
    hypergraph: HyperGraph,
    layers: int,
    ansatz_template: Optional[int],
    adaptive_optimizer=False,
) -> List[OptimizationProblem]:
    """
    Given a hypergraph and a number of layers, solve the problem using
    exact, VQE, and QAOA methods, and return a list containing two optimization
    problems (one for VQE and one for QAOA).
    """
    start_time = time.time()
    print(
        f"[START] Processing hypergraph with {len(hypergraph.nodes)} nodes and "
        f"{len(hypergraph.edges)} edges. Start time: {start_time:.2f}"
    )

    solver = HyperMaxCutSolver(
        n_layers=layers, hypergraph=hypergraph, adaptive_optimizer=adaptive_optimizer
    )

    ansatz = None
    if not adaptive_optimizer:
        ansatz = get_ansatz(
            ansatz_type=ansatz_template,
            num_qubits=hypergraph.get_n_nodes(),
            layers=layers,
        )

    # Solve exactly.
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

    # Solve using VQE.
    (
        vqe_states,
        vqe_expectation_value,
        vqe_params,
        vqe_total_steps,
        vqe_probs,
    ) = solver.solve_vqe(ansatz=ansatz)
    vqe_bitstrings = [
        int_to_bitstring(state, hypergraph.get_n_nodes()) for state in vqe_states
    ]

    # Solve using Adaptive VQE.
    (
        adapt_vqe_states,
        adapt_vqe_expectation_value,
        adapt_vqe_params,
        adapt_vqe_total_steps,
        adapt_vqe_probs,
    ) = solver.solve_adaptive_vqe()
    adapt_vqe_bitstrings = [
        int_to_bitstring(state, hypergraph.get_n_nodes()) for state in adapt_vqe_states
    ]

    # Solve using QAOA.
    (
        qaoa_states,
        qaoa_expectation_value,
        qaoa_params,
        qaoa_total_steps,
        qaoa_probs,
    ) = solver.solve_qaoa()
    qaoa_bitstrings = [
        int_to_bitstring(state, hypergraph.get_n_nodes()) for state in qaoa_states
    ]

    qaoa_circuit_with_params = solver.circuit_to_qasm(
        qaoa_params, symbolic_params=False
    )
    qaoa_circuit_with_symbols = solver.circuit_to_qasm(
        qaoa_params, symbolic_params=True
    )
    vqe_circuit_with_params = solver.circuit_to_qasm(vqe_params, symbolic_params=False)
    vqe_circuit_with_symbols = solver.circuit_to_qasm(vqe_params, symbolic_params=True)
    adapt_vqe_circuit_with_params = solver.circuit_to_qasm(
        adapt_vqe_params, symbolic_params=False
    )
    adapt_vqe_circuit_with_symbols = solver.circuit_to_qasm(
        adapt_vqe_params, symbolic_params=True
    )

    vqe_optimization_problem = HyperMaxCutOptimizationProblem(
        problem_type=OptimizationProblemType.HYPERGRAPH_CUT,
        optimization_type=OptimizationType.VQE,
        signature=hypergraph.get_signature(),
        hypergraph=hypergraph.to_dict(),
        number_of_layers=layers,
        number_of_qubits=hypergraph.get_n_nodes(),
        cost_hamiltonian=solver.get_cost_hamiltonian(),
        exact_solution=exact_solution,
        circuit_with_params=vqe_circuit_with_params,
        circuit_with_symbols=vqe_circuit_with_symbols,
        vqe_solution=QuantumSolution(
            states=vqe_states,
            expectation_value=vqe_expectation_value,
            params=vqe_params,
            bitstrings=vqe_bitstrings,
            total_optimization_steps=vqe_total_steps,
            probabilities=vqe_probs,
        ),
    )

    adapt_vqe_optimization_problem = HyperMaxCutOptimizationProblem(
        problem_type=OptimizationProblemType.HYPERGRAPH_CUT,
        optimization_type=OptimizationType.ADAPTIVE_VQE,
        signature=hypergraph.get_signature(),
        hypergraph=hypergraph.to_dict(),
        number_of_layers=layers,
        number_of_qubits=hypergraph.get_n_nodes(),
        cost_hamiltonian=solver.get_cost_hamiltonian(),
        exact_solution=exact_solution,
        circuit_with_params=adapt_vqe_circuit_with_params,
        circuit_with_symbols=adapt_vqe_circuit_with_symbols,
        vqe_solution=QuantumSolution(
            states=adapt_vqe_states,
            expectation_value=adapt_vqe_expectation_value,
            params=adapt_vqe_params,
            bitstrings=adapt_vqe_bitstrings,
            total_optimization_steps=adapt_vqe_total_steps,
            probabilities=adapt_vqe_probs,
        ),
    )

    qaoa_optimization_problem = HyperMaxCutOptimizationProblem(
        problem_type=OptimizationProblemType.HYPERGRAPH_CUT,
        optimization_type=OptimizationType.QAOA,
        signature=hypergraph.get_signature(),
        hypergraph=hypergraph.to_dict(),
        number_of_layers=layers,
        number_of_qubits=hypergraph.get_n_nodes(),
        cost_hamiltonian=solver.get_cost_hamiltonian(),
        exact_solution=exact_solution,
        circuit_with_params=qaoa_circuit_with_params,
        circuit_with_symbols=qaoa_circuit_with_symbols,
        qaoa_solution=QuantumSolution(
            states=qaoa_states,
            expectation_value=qaoa_expectation_value,
            params=qaoa_params,
            bitstrings=qaoa_bitstrings,
            total_optimization_steps=qaoa_total_steps,
            probabilities=qaoa_probs,
        ),
    )

    print(adapt_vqe_optimization_problem)
    end_time = time.time()
    elapsed = end_time - start_time
    print(
        f"[END] Processing hypergraph with {len(hypergraph.nodes)} nodes and "
        f"{len(hypergraph.edges)} edges. End time: {end_time:.2f}. "
        f"Elapsed time: {elapsed:.2f} seconds."
    )
    return [vqe_optimization_problem, qaoa_optimization_problem]


@dataclass
class HyperMaxCutOptimizationProblem(OptimizationProblem):
    hypergraph: HyperGraph = None


class HyperMaxCutDataGenerator(DataGenerator):
    """
    A data generator for the HyperMaxCut problem.

    This class generates random hypergraphs and processes them to generate solutions
    for the HyperMaxCut problem. The generated data is then saved to disk.

    Attributes:
        node_range (tuple): A tuple specifying the range of nodes in the hypergraphs.

    Methods:
        generate_data():
            Generates hypergraphs, processes them, and saves the solutions.

        __generate_hypergraphs() -> Set[HyperGraph]:
            Generates a set of random hypergraphs based on the specified node range.

        __generate_random_hypergraph(num_nodes: int, num_hyperedges: int, max_edge_size: int) -> HyperGraph:
            Generates a single random hypergraph with the specified number of nodes, hyperedges, and maximum edge size.

        _save_data(solutions: List[OptimizationProblem]):
            Saves the generated solutions to disk.
    """

    def __init__(
        self,
        layers: int,
        ansatz_template: Optional[int],
        output_path: str,
    ):
        super().__init__("hypermaxcut")
        self.node_range = (9, 11)

        self.layers = layers
        self.output_path = output_path

        self.ansatz_template = ansatz_template
        if ansatz_template:
            self.adaptive_optimizer = False
        else:
            self.adaptive_optimizer = True

    def _get_existing_signatures(self) -> Set[str]:
        """
        Returns a set of hypergraph signatures already saved in the output directory.
        Assumes the filename format is:
            {self.description}_{optimization_type}_{n_qubits}_{layers}_{signature}.json
        """
        existing_signatures = set()
        if not os.path.exists(self.output_path):
            return existing_signatures

        for filename in os.listdir(self.output_path):
            if filename.endswith(".json") and filename.startswith(self.description):
                # The signature is assumed to be the last part before ".json"
                parts = filename.split("_")
                # Remove the .json extension from the last part.
                signature_part = parts[-1].replace(".json", "")
                existing_signatures.add(signature_part)
        return existing_signatures

    def generate_data(self):
        # First, we generate the hypergraphs
        hypergraphs = self.__generate_hypergraphs()

        # Filter out hypergraphs whose signature already exists.
        existing_signatures = self._get_existing_signatures()
        filtered_hypergraphs = []
        for hg in hypergraphs:
            sig = hg.get_signature()
            if sig in existing_signatures:
                print(f"Skipping hypergraph with signature {sig} (already processed).")
            else:
                filtered_hypergraphs.append(hg)

        print(f"Strating the processing of {len(filtered_hypergraphs)} hypergraphs")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(
                    process_hypergraph,
                    hg,
                    self.layers,
                    self.ansatz_template,
                    self.adaptive_optimizer,
                )
                for hg in hypergraphs
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    solutions = future.result()
                    # Each hypergraph processing returns a list of solutions,
                    # so save them one by one.
                    for solution in solutions:
                        self._save_solution(solution)
                except Exception as exc:
                    print(f"A hypergraph processing failed with exception: {exc}")

    def __generate_hypergraphs(self) -> Set[HyperGraph]:
        hypergraphs: Set[HyperGraph] = set()

        for n_nodes in range(self.node_range[0], self.node_range[1] + 1):
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

    def _save_solution(self, solution: OptimizationProblem):
        """
        Saves a single optimization problem solution to disk.
        The filename format is:
            {self.description}_{optimization_type}_{n_qubits}_{layers}_{signature}.json
        """
        filename = (
            f"{self.description}_{solution.optimization_type}_"
            f"{solution.number_of_qubits}_{self.layers}_{solution.signature}.json"
        )

        unique_path = os.path.join(self.output_path, filename)

        with open(unique_path, "w", encoding="utf-8") as file:
            json.dump(solution, file, cls=DataclassJSONEncoder, indent=4)
