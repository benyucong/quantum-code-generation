from typing import Dict

import dimod
import jax
import jax.numpy as jnp
import optax
import pennylane as qml
from dimod import BinaryQuadraticModel, Vartype
from pennylane import numpy as np
from pennylane.transforms import compile as qml_compile
from qiskit import qasm3

from src.data_classes import OptimizationType
from src.optimization.ansatz import Ansatz
from src.solver import Solver
from src.utils import (
    basis_vector_to_bitstring,
    copy_circuit_with_new_measurement,
    int_to_bitstring,
    pennylane_to_qiskit,
    replace_h_rz_h_with_rx,
    smallest_eigenpairs,
    smallest_sparse_eigenpairs,
)


class BinaryOptimizationProblem(Solver):
    """
    Input
    binary_polynomial: dimod.BinaryPolynomial, dimod.BinaryQuadraticModel, or qml.ops.op_math.LinearCombination
                    p: number of layers in the QAOA or VQE circuit
    """

    def __init__(
        self,
        binary_polynomial: BinaryQuadraticModel,
        description: str,
        p=1,
        device_type="cpu",
    ):
        self.description = description
        self.binary_polynomial = binary_polynomial
        self.variables = sorted(list(binary_polynomial.variables), key=lambda x: str(x))

        # Basic vars
        self.n_qubits = len(self.variables)
        self.coeffs = []
        self.observables = []
        self.p = p
        self.init_params = 0.01 * np.random.rand(2, p, requires_grad=True)
        self.smallest_bitstrings = []
        self.qaoa_circuit = None
        self.vqe_circuit = None
        self.adaptive_vqe_circuit = None
        self.smallest_eigenvectors = None
        self.smallest_eigenvalues = None
        self.smallest_bitstrings = None
        self.adaptive_circuits = []
        self.adaptive_gradients = []
        self.device_type = device_type

        # This translates the binary polynomial to a spin Hamiltonian
        if isinstance(self.binary_polynomial, dimod.BinaryPolynomial):
            if self.binary_polynomial.vartype == Vartype.BINARY:
                h, J, offset = self.binary_polynomial.to_hising()
                for var in h:
                    J[(var,)] = h[var]
                self.binary_polynomial = dimod.BinaryPolynomial(J, Vartype.SPIN)
        elif isinstance(self.binary_polynomial, dimod.BinaryQuadraticModel):
            if self.binary_polynomial.vartype == Vartype.BINARY:
                linear, quadratic, offset = self.binary_polynomial.to_ising()
                self.binary_polynomial = dimod.BinaryQuadraticModel(
                    linear, quadratic, offset, Vartype.SPIN
                )
        else:
            assert isinstance(self.binary_polynomial, qml.ops.op_math.LinearCombination)

        variables_to_qubits = {var: i for i, var in enumerate(self.variables)}
        self.variables_to_qubits = variables_to_qubits
        qubits_to_variables = {i: var for i, var in enumerate(self.variables)}
        self.qubits_to_variables = qubits_to_variables

        self._construct_cost_hamiltonian()
        self.qaoa_circuit, self.qaoa_probs_circuit = self.get_qaoa_circuits()

    def _construct_cost_hamiltonian(self):
        if isinstance(self.binary_polynomial, dimod.BinaryPolynomial):
            for var in self.binary_polynomial:
                self.coeffs.append(self.binary_polynomial[var])
                self.observables.append(
                    qml.prod(*[qml.PauliZ(self.variables_to_qubits[w]) for w in var])
                )
        elif isinstance(self.binary_polynomial, dimod.BinaryQuadraticModel):
            for var in self.binary_polynomial.quadratic:
                self.coeffs.append(self.binary_polynomial.quadratic[var])
                self.observables.append(
                    qml.PauliZ(self.variables_to_qubits[var[0]])
                    @ qml.PauliZ(self.variables_to_qubits[var[1]])
                )
            for var in self.binary_polynomial.linear:
                self.coeffs.append(self.binary_polynomial.linear[var])
                self.observables.append(qml.PauliZ(self.variables_to_qubits[var]))
        self.cost_hamiltonian = qml.ops.op_math.LinearCombination(
            self.coeffs, self.observables
        )

    def get_cost_hamiltonian(self):
        return self.cost_hamiltonian

    def _create_quantum_device(self, n_qubits: int):
        """Create appropriate quantum device based on available hardware"""
        if self.device_type == "gpu":
            try:
                return qml.device("lightning.gpu", wires=n_qubits)
            except:
                return qml.device("default.qubit", wires=n_qubits)
        return qml.device("default.qubit", wires=n_qubits)

    def get_qaoa_circuits(self):
        dev = self._create_quantum_device(self.n_qubits)

        cost_hamiltonian = self.get_cost_hamiltonian()
        mixer_hamiltonian = qml.qaoa.x_mixer(range(self.n_qubits))

        def qaoa_layer(gamma, alpha):
            qml.qaoa.cost_layer(gamma, cost_hamiltonian)
            qml.qaoa.mixer_layer(alpha, mixer_hamiltonian)

        @qml.qnode(dev, interface="jax")
        def qaoa_circuit(params):
            for wire in range(self.n_qubits):
                qml.Hadamard(wires=wire)
            qml.layer(qaoa_layer, self.p, params[0], params[1])
            return qml.expval(cost_hamiltonian)

        @qml.qnode(dev, interface="jax")
        def qaoa_probs_circuit(params):
            for wire in range(self.n_qubits):
                qml.Hadamard(wires=wire)
            qml.layer(qaoa_layer, self.p, params[0], params[1])
            return qml.probs(wires=range(self.n_qubits))

        # Compile the QAOA circuit to some specific gate set
        # It seems that Pennylane compiler is too eager to decompose,
        # since it unnecessarily applies the rule RX = H RZ H
        allowed_gates = ["CNOT", "RZ", "RX", "Hadamard"]
        dispatched_transform = qml.transform(replace_h_rz_h_with_rx)
        qaoa_circuit = qml_compile(qaoa_circuit, basis_set=allowed_gates)
        qaoa_circuit = qml_compile(qaoa_circuit, pipeline=[dispatched_transform])

        qaoa_probs_circuit = qml_compile(qaoa_probs_circuit, basis_set=allowed_gates)
        qaoa_probs_circuit = qml_compile(
            qaoa_probs_circuit, pipeline=[dispatched_transform]
        )

        return qaoa_circuit, qaoa_probs_circuit

    def solve_exactly(self):
        # Solve normally if the number of qubits is less than 14
        if self.n_qubits < 14:
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
                self.smallest_bitstrings,
                first_excited_energy,
                self.smallest_eigenvectors,
            )

        # Solve with sparse eigensolver if the number of qubits is greater than 14
        cost_matrix = self.get_cost_hamiltonian().sparse_matrix(
            wire_order=range(self.n_qubits)
        )

        (
            self.smallest_eigenvalues,
            self.smallest_eigenvectors,
            first_excited_energy,
            first_excited_state,
        ) = smallest_sparse_eigenpairs(cost_matrix)

        self.smallest_bitstrings = [
            basis_vector_to_bitstring(v) for v in self.smallest_eigenvectors
        ]
        return (
            self.smallest_eigenvalues,
            self.smallest_bitstrings,
            first_excited_energy,
            self.smallest_eigenvectors,
        )

    def set_smallest_bitrings(self, smallest_bitstrings):
        self.smallest_bitstrings = smallest_bitstrings

    def solve_with_qaoa(self) -> Dict:
        print("Solving with QAOA")
        solver = optax.adamw(learning_rate=0.01)

        params = self.init_params.copy()
        params = jnp.array(params)

        total_steps = 0
        attempts = 0
        limit_steps = 500
        success = False
        jit_circuit = jax.jit(self.qaoa_circuit)

        while True:
            steps = 10
            opt_state = solver.init(params)
            for _ in range(steps):
                grad = jax.grad(jit_circuit)(params)
                updates, opt_state = solver.update(grad, opt_state, params)
                params = optax.apply_updates(params, updates)

            total_steps += steps
            probs = self.qaoa_probs_circuit(params)
            most_probable_state = np.argsort(probs)[-1]
            most_probable_state = int_to_bitstring(most_probable_state, self.n_qubits)

            if most_probable_state in self.smallest_bitstrings:
                success = True
                break
            if total_steps > limit_steps:
                print("Optimization did not converge")
                print("Trying with a new initialization")
                self.init_params = jnp.array(0.01 * np.pi * np.random.rand(2, self.p))
                params = self.init_params.copy()
                total_steps = 0
                attempts += 1
            if attempts > 3:
                print(
                    "Optimization did not converge to the known optimal solution after ",
                    attempts,
                    " attempts.",
                )
                break

        expectation_value = self.qaoa_circuit(params)
        two_most_probable_states = np.argsort(probs)[-2:]
        states_probs = [probs[i] for i in two_most_probable_states]

        # Round parameters before returning
        if isinstance(params, (jnp.ndarray, np.ndarray)):
            params = jnp.round(params, decimals=4)

        return {
            "two_most_probable_states": two_most_probable_states,
            "expectation_value": expectation_value,
            "params": params,
            "total_steps": total_steps,
            "states_probs": states_probs,
            "success": success,
        }

    def solve_with_vqe(self, ansatz_id) -> Dict:
        print("Solving with VQE")
        ansatz = Ansatz(ansatz_id, self.n_qubits, self.p)
        circuit = ansatz.get_circuit()
        single_qubit_params_shape, two_qubit_params_shape = (
            ansatz.get_parameter_shapes()
        )
        dev = self._create_quantum_device(self.n_qubits)
        cost_hamiltonian = self.get_cost_hamiltonian()

        if two_qubit_params_shape is None:
            params = jnp.asarray(0.01 * np.random.rand(*single_qubit_params_shape))
        else:
            single_qubit_params = jnp.asarray(
                0.01 * np.random.rand(*single_qubit_params_shape)
            )
            single_qubit_params_size = single_qubit_params.size
            two_qubit_params = jnp.asarray(
                0.01 * np.random.rand(*two_qubit_params_shape)
            )
            # Create a single array of parameters of shape [single_qubit_params, two_qubit_params]
            params = jnp.concatenate(
                [single_qubit_params.flatten(), two_qubit_params.flatten()]
            )

        if two_qubit_params_shape is None:

            @qml.qnode(dev, interface="jax")
            def vqe_circuit(params):
                circuit(params)
                return qml.expval(cost_hamiltonian)

            @qml.qnode(dev, interface="jax")
            def vqe_probs_circuit(params):
                circuit(params)
                return qml.probs()
        else:

            @qml.qnode(dev, interface="jax")
            def vqe_circuit(params):
                single_qubit_params, two_qubit_params = jnp.split(
                    params, [single_qubit_params_size]
                )
                single_qubit_params = single_qubit_params.reshape(
                    single_qubit_params_shape
                )
                two_qubit_params = two_qubit_params.reshape(two_qubit_params_shape)
                circuit(single_qubit_params, two_qubit_params)
                return qml.expval(cost_hamiltonian)

            @qml.qnode(dev, interface="jax")
            def vqe_probs_circuit(params):
                single_qubit_params, two_qubit_params = jnp.split(
                    params, [single_qubit_params_size]
                )
                single_qubit_params = single_qubit_params.reshape(
                    single_qubit_params_shape
                )
                two_qubit_params = two_qubit_params.reshape(two_qubit_params_shape)
                circuit(single_qubit_params, two_qubit_params)
                return qml.probs()

        solver = optax.adamw(learning_rate=0.01)
        probs = vqe_probs_circuit(params)
        self.vqe_circuit = vqe_circuit
        total_steps = 0
        attempts = 0
        limit_steps = 500
        success = False
        jit_circuit = jax.jit(self.vqe_circuit)

        while True:
            steps = 10
            opt_state = solver.init(params)
            for _ in range(steps):
                grad = jax.grad(jit_circuit)(params)
                updates, opt_state = solver.update(grad, opt_state, params)
                params = optax.apply_updates(params, updates)

            total_steps += steps
            probs = vqe_probs_circuit(params)

            most_probable_state = np.argsort(probs)[-1]
            most_probable_state = int_to_bitstring(most_probable_state, self.n_qubits)

            if most_probable_state in self.smallest_bitstrings:
                success = True
                break

            if total_steps > limit_steps:
                print("Optimization did not converge")
                print("Trying with a new initialization")

                if two_qubit_params_shape is None:
                    params = jnp.array(
                        0.01 * np.random.rand(*single_qubit_params_shape)
                    )
                else:
                    single_qubit_params = jnp.array(
                        0.01 * np.random.rand(*single_qubit_params_shape)
                    )
                    single_qubit_params_size = single_qubit_params.size
                    two_qubit_params = jnp.array(
                        0.01 * np.random.rand(*two_qubit_params_shape)
                    )
                    params = jnp.concatenate(
                        [single_qubit_params.flatten(), two_qubit_params.flatten()]
                    )

                total_steps = 0
                attempts += 1

            if attempts > 2:
                print(
                    "Optimization did not converge to the known optimal solution after ",
                    attempts,
                    " attempts.",
                )
                break

        probs = vqe_probs_circuit(params)
        expectation_value = self.vqe_circuit(params)
        two_most_probable_states = np.argsort(probs)[-2:]
        states_probs = [probs[i] for i in two_most_probable_states]

        if two_qubit_params_shape is None:
            single_qubit_params = params
            two_qubit_params = None
        else:
            single_qubit_params, two_qubit_params = jnp.split(
                params, [single_qubit_params_size]
            )
            single_qubit_params = single_qubit_params.reshape(single_qubit_params_shape)
            two_qubit_params = two_qubit_params.reshape(two_qubit_params_shape)

        # Round all parameters before returning
        if isinstance(params, (jnp.ndarray, np.ndarray)):
            params = jnp.round(params, decimals=4)
            if two_qubit_params_shape is None:
                single_qubit_params = params
                two_qubit_params = None
            else:
                single_qubit_params, two_qubit_params = jnp.split(
                    params, [single_qubit_params_size]
                )
                single_qubit_params = jnp.round(
                    single_qubit_params.reshape(single_qubit_params_shape), decimals=4
                )
                two_qubit_params = jnp.round(
                    two_qubit_params.reshape(two_qubit_params_shape), decimals=4
                )

        return {
            "two_most_probable_states": two_most_probable_states,
            "expectation_value": expectation_value,
            "params": params,
            "total_steps": total_steps,
            "states_probs": states_probs,
            "success": success,
            "single_qubit_params": single_qubit_params,
            "two_qubit_params": two_qubit_params,
        }

    @staticmethod
    def create_adaptive_circuit(n_qubits, cost_hamiltonian):
        """Create a base adaptive VQE circuit."""
        dev = qml.device("default.qubit", wires=n_qubits)

        @qml.qnode(dev)
        def circuit():
            for wire in range(n_qubits):
                qml.Hadamard(wires=wire)
            return qml.expval(cost_hamiltonian)

        return circuit

    def solve_with_adaptive_vqe(self) -> Dict:
        print("Solving with Adaptive VQE")
        # Round initial operator parameters to 4 decimal places
        operator_pool = [qml.RX(round(0.001, 4), i) for i in range(self.n_qubits)]
        operator_pool += [qml.RY(round(0.001, 4), i) for i in range(self.n_qubits)]
        operator_pool += [qml.RZ(round(0.001, 4), i) for i in range(self.n_qubits)]
        for i in range(self.n_qubits):
            for j in range(self.n_qubits):
                if i != j:
                    operator_pool.append(qml.CRZ(round(0.001, 4), wires=[i, j]))
                    operator_pool.append(qml.CRX(round(0.001, 4), wires=[i, j]))
                    operator_pool.append(qml.CRY(round(0.001, 4), wires=[i, j]))

        dev = self._create_quantum_device(self.n_qubits)
        opt = qml.AdaptiveOptimizer()
        cost_hamiltonian = self.get_cost_hamiltonian()

        adaptive_vqe_circuit = self.create_adaptive_circuit(
            self.n_qubits, cost_hamiltonian
        )

        total_steps = 0
        max_steps = 100
        adaptive_circuits = []
        for i in range(max_steps):
            adaptive_vqe_circuit, energy, gradient = opt.step_and_cost(
                adaptive_vqe_circuit, operator_pool, drain_pool=True
            )
            print(
                f"Step {i} for problem {self.description} qubits: {self.n_qubits}, Energy: {round(float(energy), 4)}, Gradient: {round(float(gradient), 4)}"
            )

            # Store rounded values
            circuit_qasm = qasm3.dumps(
                pennylane_to_qiskit(
                    adaptive_vqe_circuit,
                    self.n_qubits,
                    params=None,
                    symbolic_params=False,
                    adapt_vqe=True,
                )
            )
            adaptive_circuits.append(circuit_qasm)
            self.adaptive_gradients.append(round(float(gradient), 4))
            total_steps += 1
            if float(gradient) < 3e-3:  # Compare with rounded gradient
                break

        self.adaptive_circuits = adaptive_circuits

        # fig, ax = qml.draw_mpl(adaptive_vqe_circuit)()
        # fig.savefig("adaptive_vqe_circuit.png")

        self.adaptive_vqe_circuit = adaptive_vqe_circuit
        expectation_value = adaptive_vqe_circuit()
        probs_circuit = copy_circuit_with_new_measurement(
            adaptive_vqe_circuit, qml.probs
        )

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

        return {
            "two_most_probable_states": most_probable_states,
            "expectation_value": expectation_value,
            "total_steps": total_steps,
            "states_probs": states_probs,
            "success": success,
        }

    def get_circuits(self):
        return self.qaoa_circuit, self.vqe_circuit, self.adaptive_vqe_circuit

    def circuit_to_qasm(
        self,
        optimization_type: OptimizationType,
        params=None,
        symbolic_params=True,
        adapt_vqe=False,
    ):
        circuit = None
        if optimization_type == OptimizationType.QAOA:
            circuit = self.qaoa_circuit
        elif optimization_type == OptimizationType.VQE:
            circuit = self.vqe_circuit
        elif optimization_type == OptimizationType.ADAPTIVE_VQE:
            circuit = self.adaptive_vqe_circuit

        if circuit is None:
            raise ValueError(
                f"No circuit defined for optimization type {optimization_type}"
            )

        qiskit_circuit = pennylane_to_qiskit(
            circuit,
            self.n_qubits,
            params=params,
            symbolic_params=symbolic_params,
            adapt_vqe=adapt_vqe,
        )
        return qasm3.dumps(qiskit_circuit)

    def get_number_of_qubits(self):
        return self.n_qubits

    def get_number_of_layers(self):
        return self.p

    def get_variables_to_qubits(self):
        return self.variables_to_qubits

    def get_adaptive_circuits(self):
        adaptive_circuits_qasm = []
        for circuit in self.adaptive_circuits:
            qiskit_circuit = pennylane_to_qiskit(
                circuit, self.n_qubits, params=None, symbolic_params=False
            )
            qasm = qasm3.dumps(qiskit_circuit)
            adaptive_circuits_qasm.append(qasm)
        return adaptive_circuits_qasm

    def get_adaptive_gradients(self):
        return self.adaptive_gradients
