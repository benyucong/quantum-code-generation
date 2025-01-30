import pennylane as qml
from pennylane import numpy as np
from qiskit.qasm3 import dumps
import argparse
import json

GRAPH = [(0, 1), (1, 2), (1, 3), (2, 3)]
N_WIRES = 4

dev = qml.device("qiskit.aer", wires=N_WIRES, shots=20)

type CircuitDescription = tuple[list[tuple[int, int]], int, str, str]


def write_qaoa_json(circuits: list[CircuitDescription], filename="qaoa_data.json"):
    """
    Writes a JSON file containing the specified data in the format:
    {
        "graph": "{input1}",
        "wires": "{input2}",
        "problem": "{input3}",
        "qasm_circuit": "{input4}"
    }
    """
    data = []
    for circuit_desc in circuits:
        graph_input, wires_input, problem_input, qasm_input = circuit_desc
        data.append(
            {
                "graph": str(graph_input),
                "wires": str(wires_input),
                "problem": str(problem_input),
                "qasm_circuit": str(qasm_input),
            }
        )

    path_to_file = f"src/data/{filename}"
    with open(path_to_file, "w") as f:
        json.dump(data, f, indent=2)


# QAOA parameters
def parse_args():
    parser = argparse.ArgumentParser(description="QAOA Max-Cut")
    parser.add_argument("--layers", type=int, default=2, help="Number of layers")
    return parser.parse_args()


# unitary operator U_B with parameter beta
def U_B(beta: float) -> None:
    for wire in range(N_WIRES):
        qml.RX(2 * beta, wires=wire)


# unitary operator U_C with parameter gamma
def U_C(gamma: float) -> None:
    for edge in GRAPH:
        qml.CNOT(wires=edge)
        qml.RZ(gamma, wires=edge[1])
        qml.CNOT(wires=edge)


def bitstring_to_int(bit_string_sample: str) -> int:
    return int(2 ** np.arange(len(bit_string_sample)) @ bit_string_sample[::-1])


@qml.qnode(dev)
def circuit(gammas, betas, return_samples=False):
    # apply Hadamards to get the n qubit |+> state
    for wire in range(N_WIRES):
        qml.Hadamard(wires=wire)
    # p instances of unitary operators
    for gamma, beta in zip(gammas, betas):
        U_C(gamma)
        U_B(beta)

    if return_samples:
        # sample bitstrings to obtain cuts
        return qml.sample()
    # during the optimization phase we are evaluating the objective using expval
    C = qml.sum(*(qml.Z(w1) @ qml.Z(w2) for w1, w2 in GRAPH))
    return qml.expval(C)


def objective(params) -> float:
    """Minimize the negative of the objective function C by postprocessing the QNnode output."""
    return -(len(GRAPH) - circuit(*params))


# QAOA optimization
def qaoa_maxcut(
    n_layers: int,
    steps=50,
) -> str:
    print(f"\n Performing QAOA with {n_layers} layers using {N_WIRES} qubits")

    # Initialize the parameters near zero
    init_params = 0.01 * np.random.rand(2, n_layers, requires_grad=True)

    # Initialize optimizer
    optimizer = qml.AdagradOptimizer(stepsize=0.5)

    # Optimize parameters in objective
    params = init_params.copy()
    for i in range(steps):
        params = optimizer.step(objective, params)
        if (i + 1) % 5 == 0:
            print(f"Objective after step {i + 1:3d}: {-objective(params): .5f}")

    # Sample 100 bitstrings by setting return_samples=True and the QNode shot count to 100
    bitstrings = circuit(*params, return_samples=True, shots=100)

    print(qml.draw(circuit)([params[0]], [params[1]], return_samples=False))

    # convert the samples bitstrings to integers
    sampled_ints = [bitstring_to_int(string) for string in bitstrings]

    # print optimal parameters and most frequently sampled bitstring
    counts = np.bincount(np.array(sampled_ints))
    most_freq_bit_string = np.argmax(counts)
    print(f"Optimized parameter vectors:\ngamma: {params[0]}\nbeta:  {params[1]}")
    print(f"Most frequently sampled bit string is: {most_freq_bit_string:04b}")

    qiskit_circuit = dev._circuit

    qasm3_code = dumps(qiskit_circuit)

    return qasm3_code


def main(n_layers_max: int) -> None:
    global dev

    data = []
    for n_layers in range(1, n_layers_max + 1):
        circuit = qaoa_maxcut(n_layers)
        data.append((GRAPH, N_WIRES, "Max-Cut", circuit))

    write_qaoa_json(data)


if __name__ == "__main__":
    args = parse_args()
    n_layers = args.layers
    main(n_layers)
