from ast import List
import json
import sys
from typing import Any, Dict
import numpy as np

import pennylane as qml

from qiskit import transpile, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse

from computations import compute_relative_entropy
from optimization import optimize_problem

def int_to_bitstring(i: int, n_qubits: int) -> str:
    """Convert an integer i to a bitstring with n_qubits bits."""
    return format(i, "0" + str(n_qubits) + "b")

def get_probability_distribution(circuit: QuantumCircuit, simulator: AerSimulator):
    """
    Get the probaility distribution for a circuit

    Args:
        circuit (QuantumCircuit): The Qiskit quantum circuit to simulate.
        simulator (AerSimulator): The Simulator. 

    Returns:
        list: probabilities
    """
    sim_circuit = circuit.remove_final_measurements(inplace=False)
    sim_circuit.save_statevector()

    result = simulator.run(sim_circuit).result()
    statevector = result.get_statevector(experiment=sim_circuit)  

    probs = statevector.probabilities().tolist()

    return probs

def evaluate_qiskit_circuit(circuit: QuantumCircuit, simulator: AerSimulator):
    """
    Simulates a Qiskit QuantumCircuit and returns the probability distribution
    and the most probable state (bitstring).

    Args:
        circuit (QuantumCircuit): The Qiskit quantum circuit to simulate.
        simulator (AerSimulator): The Simulator. 

    Returns:
        tuple: (probabilities, most_probable_bitstring)
    """
    probs = get_probability_distribution(circuit, simulator)

    most_probable_state_index = np.argmax(probs)
    bitstring = int_to_bitstring(most_probable_state_index, circuit.num_qubits)

    return probs, bitstring


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


def is_most_probable_state_correct(
    sample: Dict[str, Any], most_probable_state: str
) -> bool:
    """
    Check if the most probable state obtained from the simulation is correct.
    """
    most_probable_states_bitstrings = sample["dataset_metrics"]["solution"]["bitstrings"]
    return most_probable_state in most_probable_states_bitstrings


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


def compare_solution(sim_probs, solution_probs):
    """
    Compares simulated probabilities with the solution probabilities.
    """
    relative_entropy = compute_relative_entropy(sim_probs, solution_probs)
    return {
        "relative_entropy": relative_entropy,
    }


def process_circuits(
    json_file: str, output_file=None, summary_file=None, relative_entropy_threshold=0.1
):
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
        # Becuase json.loads is not recursive parse
        sample["dataset_metrics"]["solution"] = json.loads(sample["dataset_metrics"]["solution"])

        generated_qasm = sample.get("generated_circuit", "")
        # generated_qasm = sample.get("dataset_metrics").get("optimal_circuit")

        # ---- Init new params ----
        sample["qasm_valid"] = False
        sample["statevector"] = None
        sample["parse_error"] = None
        sample["simulation_error"] = None
        sample["comparison"] = None

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

        # --- 2) Add Measurement Operations ---
        n_qubits = circuit.num_qubits

        # --- 3) Simulate and Get Statevector/Probabilities ---
        try:
            probs, bitstring = evaluate_qiskit_circuit(circuit, simulator)
            sample["most_probable_state_generated"] = bitstring
            sample["is_most_probable_state_correct"] = is_most_probable_state_correct(sample, bitstring)

        except Exception as err:
            print(f"[FAIL] Simulation failed for circuit: {idx}: {err}")
            sample["simulation_error"] = str(err)
            results.append(sample)
            continue

        # --- 4) Compare with Expected Solution ---
        solution_circuit = parse_qasm_from_str(sample.get("dataset_metrics").get("optimal_circuit"))
        solution_probs = get_probability_distribution(solution_circuit, simulator)
        sample["comparison"] = compare_solution(probs, solution_probs)


        results.append(sample)

    # ---- 5) Summary Statistics ----
    total_samples = len(results)
    compiled_count = sum(1 for sample in results if sample.get("qasm_valid") is True)
    correct_state_count = sum(
        1 for sample in results if sample.get("is_most_probable_state_correct") is True
    )
    correct_samples = [
        sample["sample_index"]
        for sample in results
        if sample.get("is_most_probable_state_correct") is True
    ]

    samples_below_threshold = []
    for sample in results:
        if sample.get("simulation_error") is None:
            comp = sample.get("comparison")
            if comp and "relative_entropy" in comp:
                if comp["relative_entropy"] < relative_entropy_threshold:
                    samples_below_threshold.append(sample["sample_index"])

    summary_stats = {
        "total_samples": total_samples,
        "compiled_successfully": compiled_count,
        "correct_state_count": correct_state_count,
        "correct_samples": correct_samples,
        "relative_entropy_threshold": relative_entropy_threshold,
        "samples_below_entropy_threshold": {
            "count": len(samples_below_threshold),
            "sample_indexes": samples_below_threshold,
        },
    }

    print("\nSummary Statistics:")
    for key, value in summary_stats.items():
        print(f"{key}: {value}")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Processed circuits saved to {output_file}")
    else:
        print(json.dumps(results, indent=2))

    if summary_file:
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_stats, f, indent=2)
        print(f"Summary statistics saved to {summary_file}")
    else:
        print(json.dumps(summary_stats, indent=2))


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python validate_qasm.py <input_json_file> [<output_json_file>] [<summary_output_file>]"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    summary_file = sys.argv[3] if len(sys.argv) > 3 else None
    process_circuits(input_file, output_file, summary_file)


if __name__ == "__main__":
    main()
