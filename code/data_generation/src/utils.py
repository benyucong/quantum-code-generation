from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import pickle
import re
from networkx import weisfeiler_lehman_graph_hash
import pennylane as qml
from pennylane import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from pennylane_qiskit import AerDevice
import scipy
import dataclasses
import json

from pennylane import numpy as np
from pennylane.ops.op_math import LinearCombination

np.random.seed(0)

from pennylane.tape import QuantumScript, QuantumScriptBatch
from pennylane.typing import PostprocessingFn


class DataclassJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for encoding dataclass objects, numpy arrays, and LinearCombination objects.

    This encoder extends the default `json.JSONEncoder` to handle additional types:
    - Dataclass objects are converted to dictionaries using `dataclasses.asdict`.
    - Numpy arrays are converted to lists using `tolist`.
    - LinearCombination objects are converted to strings using `str`.

    Methods:
        default(obj): Overrides the default method to provide custom serialization for specific types.
    """

    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if hasattr(obj, "tolist") and callable(obj.tolist):
            try:
                return obj.tolist()
            except Exception:
                pass
        if isinstance(obj, LinearCombination):
            return str(obj)
        return super().default(obj)


def remove_zero_rotations(qc):
    new_qc = QuantumCircuit(qc.num_qubits, qc.num_clbits)
    for instr, qargs, cargs in qc.data:
        if instr.name in ["rx", "ry", "rz", "crx", "cry", "crz"] and np.isclose(
            instr.params[0], 0, atol=1e-10
        ):
            continue  # Skip zero rotation gates
        new_qc.append(instr, qargs, cargs)
    return new_qc


def copy_circuit_with_new_measurement(circuit, new_measurement):
    original_device = circuit.device

    def new_qnode_function():
        tape = qml.workflow.construct_tape(circuit)()
        for op in tape.operations:
            qml.apply(op)
        return new_measurement(wires=original_device.wires)

    return qml.QNode(new_qnode_function, original_device)


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


def smallest_eigenpairs(A):
    """
    Return the smallest eigenvalues and eigenvectors of a matrix A
    Returns always at least two eigenvalues and eigenvectors,
    even if the second solution is not optimal.
    The non-zero difference between the two smallest eigenvalues
    can describe hardness of the optimization problem.
    """

    eigenvalues, eigenvectors = scipy.linalg.eig(A)
    eigenvalues = np.real(eigenvalues)
    eigenvectors = np.real(eigenvectors)
    idx = np.argsort(eigenvalues)
    smallest_eigenvalues = []
    smallest_eigenvectors = []

    smallest_eigenvalue = eigenvalues[idx[0]]
    smallest_eigenvalues.append(smallest_eigenvalue)
    smallest_eigenvectors.append(eigenvectors[:, idx[0]])

    first_excited_energy = None
    first_excited_state = None

    # Find all smallest eigenvalues and eigenvectors
    for i in range(1, len(eigenvalues)):
        if eigenvalues[idx[i]] == smallest_eigenvalue:
            smallest_eigenvalues.append(eigenvalues[idx[i]])
            smallest_eigenvectors.append(eigenvectors[:, idx[i]])
        else:
            first_excited_energy = eigenvalues[idx[i]]
            first_excited_state = eigenvectors[:, idx[i]]
            break

    return (
        smallest_eigenvalues,
        smallest_eigenvectors,
        first_excited_energy,
        first_excited_state,
    )


def smallest_sparse_eigenpairs(A):
    """
    Return the smallest eigenvalues and eigenvectors of a sparse matrix A
    Returns always at least two eigenvalues and eigenvectors,
    even if the second solution is not optimal.
    The non-zero difference between the two smallest eigenvalues
    can describe hardness of the optimization problem.
    """

    eigenvalues, eigenvectors = scipy.sparse.linalg.eigsh(A, k=6, which="SA")
    idx = np.argsort(eigenvalues)
    smallest_eigenvalues = []
    smallest_eigenvectors = []

    smallest_eigenvalue = eigenvalues[idx[0]]
    smallest_eigenvalues.append(smallest_eigenvalue)
    smallest_eigenvectors.append(eigenvectors[:, idx[0]])

    first_excited_energy = None
    first_excited_state = None

    # Find all smallest eigenvalues and eigenvectors
    for i in range(1, len(eigenvalues)):
        if eigenvalues[idx[i]] == smallest_eigenvalue:
            smallest_eigenvalues.append(eigenvalues[idx[i]])
            smallest_eigenvectors.append(eigenvectors[:, idx[i]])
        else:
            first_excited_energy = eigenvalues[idx[i]]
            first_excited_state = eigenvectors[:, idx[i]]
            break

    return (
        smallest_eigenvalues,
        smallest_eigenvectors,
        first_excited_energy,
        first_excited_state,
    )


def bitstring_to_int(bit_string_sample):
    return int(2 ** np.arange(len(bit_string_sample)) @ bit_string_sample[::-1])


def int_to_bitstring(int_sample, n_qubits):
    bits = np.binary_repr(int_sample, width=n_qubits)
    bits = np.array([1 - int(i) for i in bits])
    return "".join([str(i) for i in bits])


def basis_vector_to_bitstring(basis_vector):
    index = np.argmax(basis_vector)
    num_qubits = int(np.log2(len(basis_vector)))
    bits = np.binary_repr(index, width=num_qubits)
    bits = np.array([1 - int(i) for i in bits])
    return "".join([str(i) for i in bits])


def pennylane_to_qiskit(
    circuit, n_qubits, params=None, symbolic_params=True, adapt_vqe=False
):
    qiskit_device = AerDevice(wires=n_qubits)
    qnode = qml.QNode(circuit.func, qiskit_device)
    if params is not None:
        qnode(params)
    else:
        qnode()
    qiskit_circuit = qiskit_device._circuit

    if symbolic_params:
        # Create a new circuit with symbolic parameters
        new_qc = QuantumCircuit(n_qubits, n_qubits)
        param_mapping = {}  # Store parameters for reuse

        for instr, qubits, clbits in qiskit_circuit.data:
            new_params = []

            # Replace constant parameters with symbolic ones
            for param in instr.params:
                if isinstance(param, (float, int)):  # Detect constants
                    if param not in param_mapping:
                        param_mapping[param] = Parameter(f"x{len(param_mapping)}")
                    new_params.append(param_mapping[param])
                else:
                    new_params.append(param)

            new_qc.append(instr.__class__(*new_params), qubits, clbits)
    else:
        new_qc = qiskit_circuit

    if adapt_vqe:
        new_qc = remove_zero_rotations(new_qc)

    return new_qc


def parametrize_qiskit_circuit(circuit):
    """
    Input: A qiskit.QuantumCircuit object with constant values inside parameterized gates
    Output: A parameterized qiskit.QuantumCircuit object with symbolic parameters and a map of constant values to shared parameters
    """
    param_circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    param_map = {}  # Maps constant values to shared parameters

    for inst in circuit.data:
        instruction, qargs, cargs = inst.operation, inst.qubits, inst.clbits
        new_params = []

        for param in instruction.params:
            if isinstance(param, (int, float)):  # Check if the param is a constant
                if param not in param_map:
                    param_map[param] = Parameter(f"θ_{len(param_map)}")
                new_params.append(param_map[param])
            else:
                new_params.append(param)  # Keep existing parameters

        param_circuit.append(instruction.__class__(*new_params), qargs, cargs)

    return param_circuit, param_map


def construct_pennylane_hamiltonian(expression):
    # Regex to extract terms (coefficient and operator sequence) with or without spaces
    term_pattern = re.compile(
        r"\s*([+-]?\d+(\.\d+)?)\s*\*\s*\(\s*((?:[XYZ]\(\d+\)\s*@\s*)*[XYZ]\(\d+\))\s*\)\s*"
    )

    # Regex to extract individual operators and indices
    operator_pattern = re.compile(r"\s*([XYZ])\s*\(\s*(\d+)\s*\)\s*")

    # Parse the expression
    terms = []
    for match in term_pattern.finditer(expression):
        coefficient = float(match.group(1))  # Convert to float
        operator_sequence = match.group(3)  # Extract operator sequence

        # Extract individual operators
        operators = [
            (m.group(1), int(m.group(2)))
            for m in operator_pattern.finditer(operator_sequence)
        ]

        terms.append({"coefficient": coefficient, "operators": operators})

    # Reconstruct the Hamiltonian
    coeffs = []
    observables = []
    for term in terms:
        coeffs.append(term["coefficient"])
        obs = None
        for pauli, qubit in term["operators"]:
            pauli_op = getattr(qml, f"Pauli{pauli}")
            if obs is None:
                obs = pauli_op(qubit)
            else:
                obs = obs @ pauli_op(qubit)
        observables.append(obs)

    return qml.ops.op_math.LinearCombination(coeffs, observables)


def load_graphs(filename):
    with open(filename, "rb") as f:
        graphs = pickle.load(f)
    return graphs


def limit_graphs(processed_graphs_folder, failed_graph_folder, graphs):
    try:
        processed_graph_files = os.listdir(processed_graphs_folder)
        failed_graph_files = os.listdir(failed_graph_folder)
    except FileNotFoundError:
        processed_graph_files = []
        failed_graph_files = []

    processed_graph_hashes = [
        file.split("_")[-1].split(".")[0] for file in processed_graph_files
    ]
    failed_graph_hashes = [
        file.split("_")[-1].split(".")[0] for file in failed_graph_files
    ]

    graphs = [
        graph
        for graph in graphs
        if weisfeiler_lehman_graph_hash(graph[0])
        not in processed_graph_hashes + failed_graph_hashes
    ]
    graphs = sorted(graphs, key=lambda x: len(x[0].nodes()))
    return graphs
