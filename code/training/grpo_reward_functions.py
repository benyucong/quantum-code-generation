import json
import re
import sys
import logging
from typing import Any, Dict, List

import numpy as np
from qiskit import transpile, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse

ANSWER_PATTERN = r"^<think>.*?</think>\s*<answer>.*?</answer>$"

logger = logging.getLogger(__name__)

def compute_relative_entropy(p, q, epsilon=1e-12) -> float:
    p = np.array(p, dtype=float)
    q = np.array(q, dtype=float)
    q = q + epsilon
    kl_divergence = np.sum(p * (np.log(p) - np.log(q)))
    return float(kl_divergence)


def int_to_bitstring(i: int, n_qubits: int) -> str:
    return format(i, "0" + str(n_qubits) + "b")


def get_probability_distribution(circuit: QuantumCircuit, simulator: AerSimulator):
    sim_circuit = circuit.remove_final_measurements(inplace=False)
    sim_circuit.save_statevector()
    result = simulator.run(sim_circuit).result()
    statevector = result.get_statevector(experiment=sim_circuit)
    probs = statevector.probabilities().tolist()
    return probs


def evaluate_qiskit_circuit(circuit: QuantumCircuit, simulator: AerSimulator):
    probs = get_probability_distribution(circuit, simulator)
    most_probable_state_index = np.argmax(probs)
    bitstring = int_to_bitstring(most_probable_state_index, circuit.num_qubits)
    return probs, bitstring


def extract_qasm(completion: str) -> str:
    completion = completion.strip()

    match = re.match(ANSWER_PATTERN, completion)

    if match:
        completion = match.group(1)
    else:
        raise ValueError("Incorrect Answer format...")

    if completion.startswith("Answer:"):
        return completion[len("Answer:") :].strip()

    return completion


def parse_qasm_circuit_from_str(completion: str):
    qasm_str = extract_qasm(completion)

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
    new_circ = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    for instr in circuit.data:
        op = instr.operation
        qubits = instr.qubits
        clbits = instr.clbits
        if hasattr(op, "to_mutable"):
            mutable_op = op.to_mutable()
        else:
            mutable_op = op
        if mutable_op.params:
            new_params = [np.random.uniform(0, 2 * np.pi) for _ in mutable_op.params]
            mutable_op.params = new_params
        new_circ.append(mutable_op, qubits, clbits)
    return new_circ


# ---------------------- REWARD FUNCTIONS -------------------------
def format_reward(completions, **kwargs):
    matches = [re.match(ANSWER_PATTERN, content) for content in completions]

    return [1.0 if match else 0.0 for match in matches]


def circuit_compile_reward(completions, **kwargs) -> List[float]:
    rewards = []
    for completion in completions:
        try:
            _ = parse_qasm_circuit_from_str(completion)

            logger.debug("Parse Successful!")

            rewards.append(1.0)
        except Exception as e:
            rewards.append(0.0)
    return rewards


def probability_distrubution_reward(completions, **kwargs) -> List[float]:
    solutions = kwargs["solution"]

    rewards = []
    simulator = AerSimulator(method="statevector")

    for generated_qasm, optimal_qasm in zip(completions, solutions):
        try:
            generated_circuit = parse_qasm_circuit_from_str(generated_qasm)
            optimal_circuit = parse_qasm_circuit_from_str(optimal_qasm)

            gen_probs = get_probability_distribution(generated_circuit, simulator)
            opt_probs = get_probability_distribution(optimal_circuit, simulator)

            rel_ent = compute_relative_entropy(gen_probs, opt_probs)
            logger.debug("Relative Entropy: %s", rel_ent)
            reward = 1.0 / (1.0 + rel_ent)
        except Exception as e:
            reward = 0.0
        rewards.append(reward)
    return rewards
