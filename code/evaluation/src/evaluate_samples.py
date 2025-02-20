from ast import List
import json
import sys
from typing import Any, Dict
import numpy as np

from qiskit import transpile, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse

from computations import compute_relative_entropy


def evaluate_statistics(results: List) -> None:
    total_samples = len(results)
    compiled_count = sum(1 for sample in results if sample.get("qasm_valid") is True)
    correct_state_count = sum(
        1 for sample in results if sample.get("is_most_probable_state_correct") is True
    )

    print("\nSummary:")
    print(f"Total circuits processed: {total_samples}")
    print(f"Circuits that compiled successfully: {compiled_count}")
    print(f"Circuits with correct state: {correct_state_count}\n")


def int_to_bitstring(i: int, n_qubits: int) -> str:
    """Convert an integer i to a bitstring with n_qubits bits."""
    return format(i, "0" + str(n_qubits) + "b")


def is_most_probable_state_correct(
    sample: Dict[str, Any], most_probable_state: str
) -> bool:
    """
    Check if the most probable state obtained from the simulation is correct.
    """

    if sample["optimization_type"] == "qaoa":
        expected_states = sample["dataset_metrics"]["qaoa_solution"]["bitstrings"]
        return most_probable_state in expected_states
    else:
        expected_states = sample["dataset_metrics"]["vqe_solution"]["bitstrings"]
        return most_probable_state in expected_states


def parse_qasm_from_str(qasm_str: str) -> QuantumCircuit:
    """
    Parses a QASM string into a Qiskit QuantumCircuit object.

    This function also checks that the QASM code is for QASM 3.0.

    Args:
        qasm_str (str): The QASM string to parse.

    Returns:
        QuantumCircuit: The parsed quantum circuit.

    Raises:
        ValueError: If the QASM string does not appear to be valid QASM 3.0 or fails to parse.
    """
    # Remove any leading marker like "Answer:"
    if qasm_str.startswith("Answer:"):
        qasm_str = qasm_str[len("Answer:") :].strip()

    # Basic check for QASM 3.0 header.
    if "OPENQASM 3.0" not in qasm_str:
        raise ValueError("QASM code does not appear to be QASM 3.0.")

    try:
        circuit = parse(qasm_str)
    except Exception as e:
        raise ValueError(
            f"Failed to parse QASM code. It might be invalid QASM 3.0 code: {e}"
        ) from e

    return circuit


def compare_solution(sim_probs, expected_solution):
    """
    Compares simulated probabilities with the expected solution from the dataset.
    expected_solution is expected to be a dict with keys "states" and "probabilities".
    Returns a dict with the simulated probabilities for the expected states,
    the expected probabilities, and the absolute differences.
    """
    expected_states = expected_solution.get("states", [])
    expected_probs = expected_solution.get("probabilities", [])
    sim_probs_for_states = [float(sim_probs[i]) for i in expected_states]
    differences = [
        abs(sim - exp) for sim, exp in zip(sim_probs_for_states, expected_probs)
    ]
    relative_entropy = compute_relative_entropy(sim_probs, expected_solution)
    return {
        "simulated_probabilities": sim_probs_for_states,
        "expected_probabilities": expected_probs,
        "absolute_differences": differences,
        "relative_entropy": relative_entropy,
    }


def process_circuits(json_file, output_file=None):
    """
    Processes a JSON file containing multiple circuit samples. For each sample, it checks whether the
    QASM code (in the 'generated_circuit' field) is valid QASM 3.0, and if so, simulates it to obtain
    the exact state vector.

    Args:
        json_file (str): Path to the input JSON file.
        output_file (str, optional): Path to save the updated JSON file. If not provided, the results
                                     will be printed to the console.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    simulator = AerSimulator(method="statevector")

    for idx, sample in enumerate(data):
        generated_qasm = sample.get("generated_circuit", "")

        # ---- Init new params ----
        sample["qasm_valid"] = False
        sample["statevector"] = None
        sample["parse_error"] = None
        sample["simulation_error"] = None
        sample["qaoa_comparison"] = None
        sample["vqe_comparison"] = None

        if not generated_qasm:
            sample["parse_error"] = "No 'generated_circuit' field found."
            results.append(sample)
            continue

        # ---- 1) CHECK IF CIRCUIT COMPILES ----
        try:
            circuit: QuantumCircuit = parse_qasm_from_str(generated_qasm)
            sample["qasm_valid"] = True
            print(f"[INFO] SUCCESS! Compile successful for cicruit: {idx}")
        except ValueError as err:
            print(f"[FAIL] Failed to compile circuit: {idx}")
            sample["parse_error"] = str(err)
            results.append(sample)
            continue

        # ---- 2) CHECK STATE VECTOR ----
        try:
            circ = transpile(circuit, simulator)
            circ.save_statevector()
            result = simulator.run(circ).result()
            statevector = result.get_statevector(circ)

            # Get Probabilities
            probs = Statevector(statevector).probabilities()

            most_probable_state = np.argsort(probs)[-1]
            most_probable_state = int_to_bitstring(
                most_probable_state, sample["dataset_metrics"]["n_qubits"]
            )

            sample["most_probable_state_generated"] = most_probable_state

            sample["is_most_probable_state_correct"] = is_most_probable_state_correct(
                sample, most_probable_state
            )
        except Exception as err:
            sample["simulation_error"] = str(err)

        # ---- 3) Compare with pre-computed ----
        if sample["simulation_error"] is None:
            if sample["dataset_metrics"]["optimization_type"] == "qaoa":
                sample["qaoa_comparison"] = compare_solution(
                    probs, sample["dataset_metrics"]["qaoa_solution"]
                )
            else:
                sample["vqe_comparison"] = compare_solution(
                    probs, sample["dataset_metrics"]["vqe_solution"]
                )

        results.append(sample)

    # ---- 4) Summary Statistics ----
    evaluate_statistics(results)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Processed circuits saved to {output_file}")
    else:
        print(json.dumps(results, indent=2))


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_qasm.py <input_json_file> [<output_json_file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    process_circuits(input_file, output_file)


if __name__ == "__main__":
    main()
