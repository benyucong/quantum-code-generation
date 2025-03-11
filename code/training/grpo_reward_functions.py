import json
import sys
from typing import Any, Dict, List
import numpy as np

import pennylane as qml

from qiskit import transpile, QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse


def compute_relative_entropy(p, q, epsilon=1e-12) -> float:
    p = np.array(p, dtype=float)
    q = np.array(q, dtype=float)
    
    # Add epsilon to q to avoid zero probabilities in the logarithm
    q = q + epsilon
    
    # Compute the KL divergence
    kl_divergence = np.sum(p * (np.log(p) - np.log(q)))
    return float(kl_divergence)

def int_to_bitstring(i: int, n_qubits: int) -> str:
    """Convert an integer i to a bitstring with n_qubits bits."""
    return format(i, "0" + str(n_qubits) + "b")

def get_probability_distribution(circuit: QuantumCircuit, simulator: AerSimulator):
    """
    Get the probability distribution for a circuit.
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
    """
    probs = get_probability_distribution(circuit, simulator)
    most_probable_state_index = np.argmax(probs)
    bitstring = int_to_bitstring(most_probable_state_index, circuit.num_qubits)
    return probs, bitstring

def parse_qasm_from_str(qasm_str: str) -> QuantumCircuit:
    """
    Parses a QASM string into a Qiskit QuantumCircuit object.
    """
    if qasm_str.startswith("Answer:"):
        qasm_str = qasm_str[len("Answer:"):].strip()
    if "OPENQASM 3.0" not in qasm_str:
        raise ValueError("QASM code does not appear to be QASM 3.0.")
    try:
        circuit = parse(qasm_str)
    except Exception as e:
        raise ValueError(f"Failed to parse QASM code. It might be invalid QASM 3.0 code: {e}") from e
    return circuit

def randomize_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    """
    Creates a new circuit with the same structure, but with randomized parameters.
    """
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
            new_params = [np.random.uniform(0, 2*np.pi) for _ in mutable_op.params]
            mutable_op.params = new_params
        new_circ.append(mutable_op, qubits, clbits)
    return new_circ

# ---------------------- REWARD FUNCTIONS -------------------------

def reward_func1(completions: List[str], target: List[str], **kwargs) -> List[float]:
    rewards = []
    for qasm_str in completions:
        try:
            _ = parse_qasm_from_str(qasm_str)
            rewards.append(1.0)
        except Exception:
            rewards.append(0.0)
    return rewards

def reward_func2(completions: List[str], target: List[str], **kwargs) -> List[float]:
    """
    Reward Function 2: Compares the probability distributions from the generated circuit and
    the target circuit. Lower relative entropy means a better match.
    The reward is computed as: reward = 1 / (1 + relative_entropy)
    """
    rewards = []
    simulator = AerSimulator(method="statevector")
    for gen_qasm, tgt_qasm in zip(completions, target):
        try:
            gen_circuit = parse_qasm_from_str(gen_qasm)
            tgt_circuit = parse_qasm_from_str(tgt_qasm)
            gen_probs = get_probability_distribution(gen_circuit, simulator)
            tgt_probs = get_probability_distribution(tgt_circuit, simulator)
            rel_ent = compute_relative_entropy(gen_probs, tgt_probs)
            reward = 1.0 / (1.0 + rel_ent)
        except Exception:
            reward = 0.0
        rewards.append(reward)
    return rewards

def reward_func3(completions: List[str], target: List[str], **kwargs) -> List[float]:
    """
    Reward Function 3: Checks if the expected value of the generated circuit is similar to
    that of the target circuit. Here, we compute the expectation value of the Z operator on
    the last qubit.
    
    The expectation is computed from the probability distribution:
      For each computational basis state, if the last bit is '0', assign +1, else -1.
    The reward is given by: exp( -|expected_value_generated - expected_value_target| )
    """
    def compute_z_expectation(probs: List[float], n_qubits: int) -> float:
        exp_val = 0.0
        for i, p in enumerate(probs):
            bitstring = int_to_bitstring(i, n_qubits)
            # Here, we use the last character of the bitstring to determine the outcome.
            value = 1 if bitstring[-1] == '0' else -1
            exp_val += p * value
        return exp_val

    rewards = []
    simulator = AerSimulator(method="statevector")
    for gen_qasm, tgt_qasm in zip(completions, target):
        try:
            gen_circuit = parse_qasm_from_str(gen_qasm)
            tgt_circuit = parse_qasm_from_str(tgt_qasm)
            gen_probs = get_probability_distribution(gen_circuit, simulator)
            tgt_probs = get_probability_distribution(tgt_circuit, simulator)
            gen_exp = compute_z_expectation(gen_probs, gen_circuit.num_qubits)
            tgt_exp = compute_z_expectation(tgt_probs, tgt_circuit.num_qubits)
            diff = abs(gen_exp - tgt_exp)
            reward = np.exp(-diff)
        except Exception:
            reward = 0.0
        rewards.append(reward)
    return rewards
