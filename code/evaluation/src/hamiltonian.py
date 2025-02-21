import pennylane as qml
from pennylane.transforms import compile as pennylane_compile
from pennylane.tape import QuantumScript, QuantumScriptBatch
from pennylane.typing import PostprocessingFn
from pennylane.ops.op_math import LinearCombination


def replace_h_rz_h_with_rx(
    tape: QuantumScript,
) -> tuple[QuantumScriptBatch, PostprocessingFn]:
    new_operations = []
    i = 0
    while i < len(tape.operations):
        op = tape.operations[i]

        # Detect pattern: H . RZ . H
        if (
            i + 2 < len(tape.operations)
            and op.name == "Hadamard"
            and tape.operations[i + 1].name == "RZ"
            and tape.operations[i + 2].name == "Hadamard"
            and op.wires == tape.operations[i + 1].wires == tape.operations[i + 2].wires
        ):
            rz_angle = tape.operations[i + 1].parameters[0]
            rx_angle = rz_angle  # RX(angle) = H . RZ(angle) . H
            new_operations.append(qml.RX(rx_angle, wires=op.wires[0]))

            # Skip the next two gates since they are replaced
            i += 3
        else:
            new_operations.append(op)
            i += 1

    # Create new transformed tape
    new_tape = tape.copy(operations=new_operations)

    def null_postprocessing(results):
        return results[0]

    return [new_tape], null_postprocessing


def create_qaoa_circuits(hamiltonian: LinearCombination, n_qubits: int, p = 1)
    """
    Creates and compiles Quantum Approximate Optimization Algorithm (QAOA) circuits.

    This method generates two QAOA circuits:
    1. `qaoa_circuit`: A circuit that returns the expected value of the cost Hamiltonian.
    2. `qaoa_probs_circuit`: A circuit that returns the probability distribution over all possible states.

    The circuits are compiled to a specific gate set to optimize performance and avoid unnecessary decompositions.

    Returns:
        tuple: A tuple containing the compiled `qaoa_circuit` and `qaoa_probs_circuit`.
    """
    dev = qml.device("default.qubit", wires=n_qubits)

    cost_hamiltonian = get_cost_hamiltonian()
    mixer_hamiltonian = qml.qaoa.x_mixer(range(n_qubits))

    def qaoa_layer(gamma, alpha):
        qml.qaoa.cost_layer(gamma, cost_hamiltonian)
        qml.qaoa.mixer_layer(alpha, mixer_hamiltonian)

    @qml.qnode(dev)
    def qaoa_circuit(*params):
        gamma, alpha = params
        for wire in range(n_qubits):
            qml.Hadamard(wires=wire)
        qml.layer(qaoa_layer, p, gamma, alpha)
        return qml.expval(cost_hamiltonian)

    @qml.qnode(dev)
    def qaoa_probs_circuit(*params):
        gamma, alpha = params
        for wire in range(n_qubits):
            qml.Hadamard(wires=wire)
        qml.layer(qaoa_layer, p, gamma, alpha)
        return qml.probs()

    # Compile the QAOA circuit to some specific gate set
    # It seems that Pennylane compiler is too eager to decompose,
    # since it unnecessarily applies the rule RX = H RZ H
    allowed_gates = ["CNOT", "RZ", "RX", "Hadamard"]
    dispatched_transform = qml.transform(replace_h_rz_h_with_rx)
    qaoa_circuit = pennylane_compile(qaoa_circuit, basis_set=allowed_gates)
    qaoa_circuit = pennylane_compile(qaoa_circuit, pipeline=[dispatched_transform])

    qaoa_probs_circuit = pennylane_compile(qaoa_probs_circuit, basis_set=allowed_gates)
    qaoa_probs_circuit = pennylane_compile(
        qaoa_probs_circuit, pipeline=[dispatched_transform]
    )

    return qaoa_circuit, qaoa_probs_circuit
