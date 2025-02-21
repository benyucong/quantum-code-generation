from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import pennylane as qml
from pennylane import QNode


def parametrize_qiskit_circuit(circuit: QuantumCircuit) -> tuple[QuantumCircuit, dict]:
    """
    Converts a Qiskit QuantumCircuit to a parameterized version.

    Args:
        circuit (QuantumCircuit): The input quantum circuit to be parameterized.

    Returns:
        tuple: A tuple containing:
            - QuantumCircuit: The parameterized quantum circuit.
            - dict: A mapping from constant values to their corresponding shared parameters.
    """
    param_circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    param_map = {}

    for inst in circuit.data:
        instruction, qargs, cargs = inst.operation, inst.qubits, inst.clbits
        new_params = []

        for param in instruction.params:
            if isinstance(param, (int, float)):
                if param not in param_map:
                    param_map[param] = Parameter(f"θ_{len(param_map)}")
                new_params.append(param_map[param])
            else:
                new_params.append(param)

        param_circuit.append(instruction.__class__(*new_params), qargs, cargs)

    return param_circuit, param_map


def convert_qiskit_circuit_to_pennylane(
    qiskit_circuit: QuantumCircuit, param_qiskit: dict
) -> tuple[QNode, list]:
    """
    Converts a Qiskit QuantumCircuit to a PennyLane QNode.
    """
    pennylane_func = qml.from_qiskit(qiskit_circuit)
    n_qubits = qiskit_circuit.num_qubits

    dev = qml.device("default.qubit", wires=n_qubits)
    pennylane_circuit = qml.QNode(pennylane_func, dev)
    params = param_qiskit.values()

    return pennylane_circuit, params


def reconstruct_qaoa_layers(
    cost_hamiltonian: str, n_qubits: int, gamma: float, alpha: float
):
    """
    Given a cost Hamiltonian and the number of qubits, reconstruct the QAOA
    operations.

    Args:
        cost_hamiltonian: Str of Cost Hamiltonianj.
        n_qubits (int): The total number of qubits.
        gamma (float): Parameter for the cost layer.
        alpha (float): Parameter for the mixer layer.

    """
    qml.qaoa.cost_layer(gamma, cost_hamiltonian)

    mixer_hamiltonian = qml.qaoa.x_mixer(range(n_qubits))
    qml.qaoa.mixer_layer(alpha, mixer_hamiltonian)
