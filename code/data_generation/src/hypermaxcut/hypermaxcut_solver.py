import itertools
from typing import Optional
import scipy
import pennylane as qml
from pennylane import numpy as np
from pennylane.transforms import compile as pennylane_compile
from pennylane.tape import QuantumScript, QuantumScriptBatch
from pennylane.typing import PostprocessingFn
from qiskit import QuantumCircuit, qasm3
from qiskit.circuit import Parameter
from code.data_generation.src.helpers import (
    basis_vector_to_bitstring,
    copy_circuit_with_new_measurement,
    int_to_bitstring,
    smallest_eigenpairs,
    replace_h_rz_h_with_rx,
)
from pennylane_qiskit import AerDevice

from src.solver import Solver
from src.hypermaxcut.hypergraph import HyperGraph
from src.ansatz import Ansatz


class HyperMaxCutSolver(Solver):
    def __init__(
        self, n_layers: int, hypergraph: HyperGraph, adaptive_optimizer=False, p=1
    ):
        super().__init__(n_qubits=hypergraph.get_n_nodes(), layers=n_layers)

        self.hypergraph = hypergraph
        self.adaptive_optimizer = adaptive_optimizer

        # Construct the Hamiltonian
        self.coeffifiencts, self.observables = self.construct_hamiltonian()
        self.qaoa_circuit, self.qaoa_probs_circuit = self._create_qaoa_circuits()

        self.p = p
        self.adaptive_vqe_circuits = []
        self.adaptive_vqe_gradients = []

        # Initialize the circuit parameters -> random initialization
        self.init_params = 0.01 * np.random.rand(2, p, requires_grad=True)

    def construct_hamiltonian(self):
        coeffs = []
        observables = []
        for edge in self.hypergraph.edges:
            coeffs, observables = self._sum_term_in_cost_hamiltonian(edge)
            coeffs.extend(coeffs)
            observables.extend(observables)
        return coeffs, observables

    def get_cost_hamiltonian(self):
        return qml.ops.op_math.LinearCombination(self.coeffifiencts, self.observables)

    def solve_exact(self):
        cost_matrix = self.get_cost_hamiltonian().matrix(
            wire_order=range(self.n_qubits)
        )
        (
            self.smallest_eigenvalues,
            self.smallest_eigenvectors,
            first_excited_energy,
            first_excited_state,
        ) = smallest_eigenpairs(cost_matrix)

        self.smallest_bitstrings = [
            basis_vector_to_bitstring(v) for v in self.smallest_eigenvectors
        ]
        return (
            self.smallest_eigenvalues,
            self.smallest_eigenvectors,
            self.smallest_bitstrings,
            first_excited_energy,
            first_excited_state,
        )

    def solve_qaoa(self):
        opt = qml.AdagradOptimizer(stepsize=0.5)

        params = self.init_params.copy()
        probs = self.qaoa_probs_circuit(*params)

        total_steps = 0
        attempts = 0
        while True:
            steps = 10
            for _ in range(steps):
                params = opt.step(self.qaoa_circuit, *params)
            total_steps += steps
            probs = self.qaoa_probs_circuit(*params)
            # smallest_eigenvalue_now = self.qaoa_circuit(params)
            most_probable_state = np.argsort(probs)[-1]
            most_probable_state = int_to_bitstring(most_probable_state, self.n_qubits)
            # print(f"Most probable state: {most_probable_state} and smallest eigenvalue: {smallest_eigenvalue_now} and {self.smallest_bitstrings}")
            if most_probable_state in self.smallest_bitstrings:
                break
            if total_steps > 1000:
                print("Optimization did not converge")
                print("Trying with a new initialization")
                self.init_params = np.pi * np.random.rand(2, self.p, requires_grad=True)
                params = self.init_params.copy()
                total_steps = 0
                attempts += 1
            if attempts > 10:
                print(
                    "Optimization did not converge to the known optimal solution after ",
                    attempts,
                    " attempts.",
                )
                print("Returning the best solution found so far")
                break

        # probs = self.qaoa_probs_circuit(params)
        smallest_eigenvalue = self.qaoa_circuit(*params)
        two_most_probable_states = np.argsort(probs)[-2:]
        states_probs = [probs[i] for i in two_most_probable_states]

        return (
            two_most_probable_states,
            smallest_eigenvalue,
            params,
            total_steps,
            states_probs,
        )

    def solve_vqe(self, ansatz: Optional[Ansatz]):
        circuit = ansatz.get_circuit()
        single_qubit_params_shape, two_qubit_params_shape = (
            ansatz.get_parameter_shapes()
        )
        dev = qml.device("default.qubit", wires=self.n_qubits)
        cost_hamiltonian = self.get_cost_hamiltonian()

        if two_qubit_params_shape is None:

            @qml.qnode(dev)
            def vqe_circuit(single_qubit_params):
                circuit(single_qubit_params)
                return qml.expval(cost_hamiltonian)

            @qml.qnode(dev)
            def vqe_probs_circuit(single_qubit_params):
                circuit(single_qubit_params)
                return qml.probs()
        else:

            @qml.qnode(dev)
            def vqe_circuit(single_qubit_params, two_qubit_params):
                circuit(single_qubit_params, two_qubit_params)
                return qml.expval(cost_hamiltonian)

            @qml.qnode(dev)
            def vqe_probs_circuit(single_qubit_params, two_qubit_params):
                circuit(single_qubit_params, two_qubit_params)
                return qml.probs()

        opt = qml.AdagradOptimizer(stepsize=0.5)
        single_qubit_params = 0.01 * np.random.rand(*single_qubit_params_shape)

        if two_qubit_params_shape is not None:
            two_qubit_params = 0.01 * np.random.rand(*two_qubit_params_shape)
            probs = vqe_probs_circuit(single_qubit_params, two_qubit_params)
        else:
            probs = vqe_probs_circuit(single_qubit_params)

        self.vqe_circuit = vqe_circuit
        total_steps = 0
        attempts = 0
        while True:
            steps = 10
            for _ in range(steps):
                if two_qubit_params_shape is None:
                    single_qubit_params = opt.step(
                        self.vqe_circuit, single_qubit_params
                    )
                else:
                    single_qubit_params, two_qubit_params = opt.step(
                        self.vqe_circuit, single_qubit_params, two_qubit_params
                    )

            total_steps += steps

            if two_qubit_params_shape is None:
                probs = vqe_probs_circuit(single_qubit_params)
            else:
                probs = vqe_probs_circuit(single_qubit_params, two_qubit_params)

            most_probable_state = np.argsort(probs)[-1]
            most_probable_state = int_to_bitstring(most_probable_state, self.n_qubits)

            if most_probable_state in self.smallest_bitstrings:
                break

            if total_steps > 1000:
                print("Optimization did not converge")
                print("Trying with a new initialization")
                single_qubit_params = np.pi * np.random.rand(*single_qubit_params_shape)

                if two_qubit_params is not None:
                    two_qubit_params = np.pi * np.random.rand(*two_qubit_params_shape)

                total_steps = 0
                attempts += 1

            if attempts > 10:
                print(
                    "Optimization did not converge to the known optimal solution after ",
                    attempts,
                    " attempts.",
                )
                print("Returning the best solution found so far")
                break

        if two_qubit_params_shape is None:
            probs = vqe_probs_circuit(single_qubit_params)
            smallest_eigenvalue = self.vqe_circuit(single_qubit_params)
        else:
            probs = vqe_probs_circuit(single_qubit_params, two_qubit_params)
            smallest_eigenvalue = self.vqe_circuit(
                single_qubit_params, two_qubit_params
            )

        two_most_probable_states = np.argsort(probs)[-2:]
        states_probs = [probs[i] for i in two_most_probable_states]
        return (
            two_most_probable_states,
            smallest_eigenvalue,
            (single_qubit_params, two_qubit_params),
            total_steps,
            states_probs,
        )

    def solve_with_adaptive_vqe(self):
        # Construct the operator pool
        operator_pool = [qml.RX(0.001, i) for i in range(self.n_qubits)]
        operator_pool += [qml.RY(0.001, i) for i in range(self.n_qubits)]
        operator_pool += [qml.RZ(0.001, i) for i in range(self.n_qubits)]
        for i in range(self.n_qubits):
            for j in range(self.n_qubits):
                if i != j:
                    operator_pool.append(qml.CRZ(0.001, wires=[i, j]))
                    operator_pool.append(qml.CRX(0.001, wires=[i, j]))
                    operator_pool.append(qml.CRY(0.001, wires=[i, j]))

        dev = qml.device("default.qubit", wires=self.n_qubits)
        opt = qml.AdaptiveOptimizer()
        cost_hamiltonian = self.get_cost_hamiltonian()

        @qml.qnode(dev)
        def vqe_circuit():
            for wire in range(self.n_qubits):
                qml.Hadamard(wires=wire)
            return qml.expval(cost_hamiltonian)

        total_steps = 0
        for i in range(len(operator_pool)):
            vqe_circuit, energy, gradient = opt.step_and_cost(
                vqe_circuit, operator_pool, drain_pool=True
            )
            self.adaptive_vqe_circuits.append(vqe_circuit)
            self.adaptive_vqe_gradients.append(gradient)
            # if i % 3 == 0:
            # print("n = {:},  E = {:.8f} H, Largest Gradient = {:.3f}".format(i, energy, gradient))
            # print(qml.draw(vqe_circuit, decimals=None)())
            # print()
            total_steps += 1
            if gradient < 3e-3:
                break

        self.vqe_circuit = vqe_circuit
        expectation_value = vqe_circuit()
        probs_circuit = copy_circuit_with_new_measurement(vqe_circuit, qml.probs)

        # Run the QNode
        probs = probs_circuit()
        most_probable_states = np.argsort(probs)[-2:]
        most_probable_state = most_probable_states[-1]
        states_probs = [probs[i] for i in most_probable_states]
        most_probable_bitstring = int_to_bitstring(most_probable_state, self.n_qubits)

        if most_probable_bitstring in self.smallest_bitstrings:
            success = True
        else:
            success = False

        return (
            most_probable_states,
            expectation_value,
            total_steps,
            states_probs,
            success,
        )

    def pennylane_to_qiskit(self, circuit, params, symbolic_params=True):
        qiskit_device = AerDevice(wires=self.n_qubits)
        qnode = qml.QNode(circuit.func, qiskit_device)
        if len(params) == 1:
            qnode(params)
        else:
            qnode(*params)
        qiskit_circuit = qiskit_device._circuit

        if symbolic_params:
            # Create a new circuit with symbolic parameters
            new_qc = QuantumCircuit(self.n_qubits, self.n_qubits)
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

        return new_qc

    def qaoa_circuit_to_qasm(self, params, symbolic_params=True):
        rounded_params = round_params(params, decimals=4)
        qiskit_circuit = self.pennylane_to_qiskit(
            self.qaoa_circuit, rounded_params, symbolic_params
        )
        return qasm3.dumps(qiskit_circuit)

    def vqe_circuit_to_qasm(self, params, symbolic_params=True):
        rounded_params = round_params(params, decimals=4)
        qiskit_circuit = self.pennylane_to_qiskit(
            self.vqe_circuit, rounded_params, symbolic_params
        )
        return qasm3.dumps(qiskit_circuit)

    def get_qasm_circuits(self, params, symbolic_params=True):
        qaoa_qiskit_circuit = self.pennylane_to_qiskit(
            self.qaoa_circuit, params, symbolic_params
        )
        vqe_qiskit_circuit = self.pennylane_to_qiskit(
            self.vqe_circuit, params, symbolic_params
        )
        return qasm3.dumps(qaoa_qiskit_circuit), qasm3.dumps(vqe_qiskit_circuit)

    def _create_qaoa_circuits(self):
        """
        Creates and compiles Quantum Approximate Optimization Algorithm (QAOA) circuits.

        This method generates two QAOA circuits:
        1. `qaoa_circuit`: A circuit that returns the expected value of the cost Hamiltonian.
        2. `qaoa_probs_circuit`: A circuit that returns the probability distribution over all possible states.

        The circuits are compiled to a specific gate set to optimize performance and avoid unnecessary decompositions.

        Returns:
            tuple: A tuple containing the compiled `qaoa_circuit` and `qaoa_probs_circuit`.
        """
        dev = qml.device("default.qubit", wires=self.n_qubits)

        cost_hamiltonian = self.get_cost_hamiltonian()
        mixer_hamiltonian = qml.qaoa.x_mixer(range(self.n_qubits))

        def qaoa_layer(gamma, alpha):
            qml.qaoa.cost_layer(gamma, cost_hamiltonian)
            qml.qaoa.mixer_layer(alpha, mixer_hamiltonian)

        @qml.qnode(dev)
        def qaoa_circuit(*params):
            gamma, alpha = params
            for wire in range(self.n_qubits):
                qml.Hadamard(wires=wire)
            qml.layer(qaoa_layer, self.p, gamma, alpha)
            return qml.expval(cost_hamiltonian)

        @qml.qnode(dev)
        def qaoa_probs_circuit(*params):
            gamma, alpha = params
            for wire in range(self.n_qubits):
                qml.Hadamard(wires=wire)
            qml.layer(qaoa_layer, self.p, gamma, alpha)
            return qml.probs()

        # Compile the QAOA circuit to some specific gate set
        # It seems that Pennylane compiler is too eager to decompose,
        # since it unnecessarily applies the rule RX = H RZ H
        allowed_gates = ["CNOT", "RZ", "RX", "Hadamard"]
        dispatched_transform = qml.transform(replace_h_rz_h_with_rx)
        qaoa_circuit = pennylane_compile(qaoa_circuit, basis_set=allowed_gates)
        qaoa_circuit = pennylane_compile(qaoa_circuit, pipeline=[dispatched_transform])

        qaoa_probs_circuit = pennylane_compile(
            qaoa_probs_circuit, basis_set=allowed_gates
        )
        qaoa_probs_circuit = pennylane_compile(
            qaoa_probs_circuit, pipeline=[dispatched_transform]
        )

        return qaoa_circuit, qaoa_probs_circuit

    def _sum_term_in_cost_hamiltonian(self, edge):
        n_nodes = len(edge)
        assert n_nodes > 1, "An edge must have at least 2 nodes"
        coeffs = [2 ** (n_nodes - 2) - 1]
        observables = [qml.prod(*[qml.Identity(i) for i in edge])]

        for subset_size in range(2, n_nodes + 1):
            if subset_size % 2 == 0:
                for subset in itertools.combinations(edge, subset_size):
                    coeffs.append(2 ** (n_nodes - 2))
                    observables.append(qml.prod(*[qml.PauliZ(i) for i in subset]))

        return coeffs, observables


def round_params(params, decimals=4):
    return tuple(np.round(np.array(p, dtype=float), decimals=decimals) for p in params)
