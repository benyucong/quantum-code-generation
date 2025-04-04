from ast import List
import json
import sys
from typing import Any, Dict
import numpy as np
import re

import pennylane as qml

from qiskit import transpile, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse

from computations import compute_relative_entropy
from util import construct_qiskit_hamiltonian

ASSISTANT_START_STRING = "<|im_start|>assistant"
ASSISTANS_END_STRING = "<|im_end|>"

RANDOM_SAMPLING_AMOUNT = 1000


def int_to_bitstring(i: int, n_qubits: int) -> str:
    """Convert an integer i to a bitstring with n_qubits bits."""
    return format(i, "0" + str(n_qubits) + "b")


def get_probability_distribution_and_expectation_value(
    circuit: QuantumCircuit, simulator: AerSimulator, hamiltonian: str
):
    """
    Get the probability distribution for a circuit.

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
    oper = construct_qiskit_hamiltonian(hamiltonian)

    expectation_value = statevector.expectation_value(oper)
    return probs, expectation_value


def evaluate_qiskit_circuit(
    circuit: QuantumCircuit, hamiltonian: str, simulator: AerSimulator
):
    probs, expectation_value = get_probability_distribution_and_expectation_value(
        circuit, simulator, hamiltonian
    )
    most_probable_state_index = np.argmax(probs)
    bitstring = int_to_bitstring(most_probable_state_index, circuit.num_qubits)
    return probs, expectation_value, bitstring


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
    most_probable_states_bitstrings = sample["dataset_metrics"]["solution"][
        "bitstrings"
    ]
    return most_probable_state in most_probable_states_bitstrings


def parse_qasm_from_str(qasm_str: str) -> QuantumCircuit:
    qasm_str = re.sub('`', '', qasm_str)
    
    if qasm_str.startswith(ASSISTANT_START_STRING):
        qasm_str = qasm_str[
            len(ASSISTANT_START_STRING) : len(qasm_str) - len(ASSISTANS_END_STRING)
        ].strip()


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


def randomize_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Creates a new circuit with the same structure, but with random parameters
    Args:
        circuit (QuantumCircuit): The circuit to randomize.

    Returns:
        QuantumCircuit: A new circuit with randomized parameters.
    """
    new_circ = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    for instr in circuit.data:
        op = instr.operation
        qubits = instr.qubits
        clbits = instr.clbits

        # Since the operation gates are immutable -> make mutable
        if hasattr(op, "to_mutable"):
            mutable_op = op.to_mutable()
        else:
            mutable_op = op

        # If the operation has parameters, randomize them.
        if mutable_op.params:
            new_params = [np.random.uniform(0, 2 * np.pi) for _ in mutable_op.params]
            mutable_op.params = new_params

        new_circ.append(mutable_op, qubits, clbits)
    return new_circ


def compare_solution(
    sim_probs,
    solution_probs,
    expectation_value,
    solution_expectation_value,
    hamiltonian,
    circuit,
    simulator,
):
    """
    Compares simulated probabilities with the solution probabilities.
    Also compares with a circuit with random parameters
    """
    relative_entropy = compute_relative_entropy(sim_probs, solution_probs)

    cumulative_random_entropy = 0
    cumulative_expectation_value = 0
    for _ in range(RANDOM_SAMPLING_AMOUNT):
        randomized_circuit = randomize_circuit(circuit)
        randomized_probs, randomized_expectation_value = (
            get_probability_distribution_and_expectation_value(
                randomized_circuit, simulator, hamiltonian
            )
        )
        cumulative_random_entropy += compute_relative_entropy(
            randomized_probs, solution_probs
        )
        cumulative_expectation_value += randomized_expectation_value
    cumulative_expectation_value /= RANDOM_SAMPLING_AMOUNT
    random_relative_entropy = cumulative_random_entropy / RANDOM_SAMPLING_AMOUNT
    print(
        f"Expectation value of solution: {solution_expectation_value}, generated: {expectation_value}, randomized: {cumulative_expectation_value}"
    )
    return {
        "relative_entropy": relative_entropy,
        "random_relative_entropy": random_relative_entropy,
        "solution_expectation_value": solution_expectation_value,
        "generated_expectation_value": expectation_value,
        "randomized_expectation_value": cumulative_expectation_value,
    }


def process_circuits(
    json_file: str, output_file=None, summary_file=None, relative_entropy_threshold=0.1
):
    """
    Processes a JSON file containing multiple circuit samples. For each sample, it checks whether the
    QASM code (in the 'generated_circuit' field) is valid QASM 3.0, and if so, simulates it to obtain
    the exact state vector.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    simulator = AerSimulator(method="statevector")

    for idx, sample in enumerate(data):
        # Because json.loads is not recursive parse
        sample["dataset_metrics"]["solution"] = json.loads(
            sample["dataset_metrics"]["solution"]
        )

        generated_qasm = sample.get("generated_circuit", "")
        hamiltonian = sample["dataset_metrics"]["cost_hamiltonian"]
        solution_expectation_value = sample["dataset_metrics"]["solution"]["expectation_value"]

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
            print(f"[INFO] SUCCESS! Compile successful for circuit: {idx}")
        except ValueError as err:
            print(f"[FAIL] Failed to compile circuit: {idx}")
            sample["parse_error"] = str(err)
            results.append(sample)
            continue

        # --- 3) Simulate and Get Statevector/Probabilities ---
        try:
            probs, expectation_value, bitstring = evaluate_qiskit_circuit(
                circuit, hamiltonian, simulator
            )
            sample["most_probable_state_generated"] = bitstring
            sample["is_most_probable_state_correct"] = is_most_probable_state_correct(
                sample, bitstring
            )
        except Exception as err:
            print(f"[FAIL] Simulation failed for circuit: {idx}: {err}")
            sample["simulation_error"] = str(err)
            results.append(sample)
            continue

        # --- 4) Compare with Expected Solution ---
        try:
            solution_circuit = parse_qasm_from_str(
                sample.get("dataset_metrics").get("optimal_circuit")
            )
            solution_probs, solution_expectation_value = (
                get_probability_distribution_and_expectation_value(
                    solution_circuit, simulator, hamiltonian
                )
            )
            # Pass the generated circuit and simulator so that its parameters can be randomized
            sample["comparison"] = compare_solution(
                probs,
                solution_probs,
                expectation_value,
                solution_expectation_value,
                hamiltonian,
                circuit,
                simulator,
            )
        except Exception as err:
            print(f"[FAIL] Processing solution failed for circuit: {idx}: {err}")
            sample["parse_error"] = str(err)
            results.append(sample)
            continue

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
    rel_entropies = []
    random_rel_entropies = []
    expectation_values = []
    solution_expectation_values = []
    random_expectation_values = []
    for sample in results:
        if (
            sample.get("simulation_error") is None
            and sample.get("comparison") is not None
        ):
            comp = sample.get("comparison")
            if "relative_entropy" in comp:
                rel_entropies.append(comp["relative_entropy"])
                random_rel_entropies.append(comp["random_relative_entropy"])
                if comp["relative_entropy"] < relative_entropy_threshold:
                    samples_below_threshold.append(sample["sample_index"])
            if "solution_expectation_value" in comp:
                solution_expectation_values.append(comp["solution_expectation_value"])
                expectation_values.append(comp["generated_expectation_value"])
                random_expectation_values.append(comp["randomized_expectation_value"])
    # Compute average expectation values if available
    if expectation_values:
        avg_expectation_value = float(np.mean(expectation_values))
        avg_solution_expectation_value = float(np.mean(solution_expectation_values))
        avg_random_expectation_value = float(np.mean(random_expectation_values))
    else:
        avg_expectation_value = None
        avg_solution_expectation_value = None
        avg_random_expectation_value = None

    # Compute average relative entropies if available
    if rel_entropies:
        avg_rel_entropy = float(np.mean(rel_entropies))
        avg_random_rel_entropy = float(np.mean(random_rel_entropies))
        ratio = (
            avg_rel_entropy / avg_random_rel_entropy
            if avg_random_rel_entropy != 0
            else None
        )
    else:
        avg_rel_entropy = None
        avg_random_rel_entropy = None
        ratio = None

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
        "average_relative_entropy": avg_rel_entropy,
        "average_random_initial_relative_entropy": avg_random_rel_entropy,
        "average_relative_entropy_ratio": ratio,
        "average_expectation_value": avg_expectation_value,
        "average_solution_expectation_value": avg_solution_expectation_value,
        "average_random_expectation_value": avg_random_expectation_value,
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
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    summary_file = sys.argv[3] if len(sys.argv) > 3 else None
    process_circuits(input_file, output_file, summary_file)


if __name__ == "__main__":
    main()
