import re

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import BackendSampler, Estimator
from qiskit.quantum_info import Operator, SparsePauliOp, Pauli
from qiskit_aer import Aer
from qiskit_algorithms import QAOA, VQE
from qiskit_algorithms.optimizers import ADAM


def parse_hamiltonian_to_sparse_pauli_op(
    ham_str: str, num_qubits: int
) -> SparsePauliOp:
    """
    Args:
        ham_str (str): The Hamiltonian string.
        num_qubits (int): Total number of qubits (e.g. 9 if indices 0 to 8 are used).

    Returns:
        SparsePauliOp: The corresponding Qiskit operator.
    """
    # Split the string into individual terms based on the '+' symbol.
    terms = ham_str.split("+")
    pauli_list = []
    coeff_list = []

    for term in terms:
        term = term.strip()
        # Match a term of the form "coefficient * (operators)"
        match = re.match(r"([+-]?\d+(?:\.\d+)?)\s*\*\s*\((.*?)\)", term)
        if not match:
            continue
        coeff = float(match.group(1))
        op_str = match.group(2)

        pauli_label = ["I"] * num_qubits

        # Split the inner operator string on '@'
        for component in op_str.split("@"):
            component = component.strip()
            m = re.match(r"([IXYZ])\((\d+)\)", component)
            if m:
                op = m.group(1)
                idx = int(m.group(2))
                pauli_label[idx] = op

        # Reverse because Qiskit
        pauli_str = "".join(reversed(pauli_label))
        pauli_list.append(pauli_str)
        coeff_list.append(coeff)

    paulis = [Pauli(label) for label in pauli_list]
    return SparsePauliOp(paulis, coeffs=coeff_list)


class OptimizationRecorder:
    """
    Helper class that records each iteration during the optimization.
    The callback function will be passed to the optimizer.
    """

    def __init__(self):
        self.step_count = 0
        self.steps = []

    def callback(self, nfev, parameters, mean, stddev):
        """
        Callback function called at each iteration.
        """
        self.step_count += 1

        param_list = (
            parameters.tolist()
            if isinstance(parameters, np.ndarray)
            else list(parameters)
        )

        self.steps.append(
            {
                "nfev": nfev,
                "parameters": param_list,
                "mean": mean,
                "stddev": stddev,
            }
        )


def optimize_problem_q(
    ansatz: QuantumCircuit,
    hamiltonian_str: str,
    initial_params: np.ndarray,
    method: str = "vqe",
    optimizer=None,
    maxiter: int = 100,
) -> dict:
    """
    Optimize the energy of a Hamiltonian using either VQE or QAOA.

    Args:
        ansatz (QuantumCircuit): A parameterized quantum circuit used as the ansatz.
                                  (For VQE this is used directly; for QAOA, the circuit is not used
                                   as a custom ansatz but its depth is used to determine the number of layers.)
        hamiltonian_str (str): The Hamiltonian to be minimized in form of a string.
        method (str): Optimization method. Use 'vqe' for VQE or 'qaoa' for QAOA.
        optimizer: An instance of a classical optimizer (default uses COBYLA).
        maxiter (int): Maximum number of iterations for the optimizer.

    Returns:
        dict: A dictionary with the optimization results including:
              - 'optimal_value': The minimized eigenvalue (energy).
              - 'optimal_parameters': The optimal variational parameters.
              - 'step_count': Total number of optimization steps taken.
              - 'steps': A log of details for each iteration.
              - 'method': Which method was used.
    """
    if optimizer is None:
        optimizer = ADAM(maxiter=maxiter)

    hamiltonian: Operator = parse_hamiltonian_to_sparse_pauli_op(
        hamiltonian_str, ansatz.num_qubits
    )

    backend = Aer.get_backend("aer_simulator_statevector")

    seed = 42
    shots = 1024
    quantum_instance = BackendSampler(
        backend, options={"shots": shots, "seed_simulator": seed}
    )
    quantum_instance.transpile_options["seed_transpiler"] = seed
    recorder = OptimizationRecorder()

    if method.lower() == "qaoa":
        reps = ansatz.depth if ansatz.depth > 0 else 1
        algorithm = QAOA(
            sampler=quantum_instance,
            optimizer=optimizer,
            reps=reps,
            callback=recorder.callback,
        )
    elif method.lower() == "vqe":
        seed = 170
        noiseless_estimator = Estimator()
        algorithm = VQE(
            estimator=noiseless_estimator,
            ansatz=ansatz,
            optimizer=optimizer,
            callback=recorder.callback,
            initial_point=initial_params,
        )
    else:
        raise ValueError("Method must be either 'vqe' or 'qaoa'.")

    result = algorithm.compute_minimum_eigenvalue(hamiltonian)

    return {
        "optimal_value": result.eigenvalue.real
        if hasattr(result.eigenvalue, "real")
        else result.eigenvalue,
        "optimal_parameters": result.optimal_point,
        "step_count": recorder.step_count,
        "steps": recorder.steps,
        "method": method.lower(),
    }


def optimize_problem(
    ansatz: QuantumCircuit,
    hamiltonian_str: str,
    initial_params: np.ndarray,
    method: str = "vqe",
    optimizer=None,
    maxiter: int = 100,
) -> dict:
    """
    Optimize the energy of a Hamiltonian using either VQE or QAOA.

    Converts the given Qiskit Circuit to Pennylane and optimizes using both VQE and QAOA
    Args:
        ansatz (QuantumCircuit): A parameterized quantum circuit used as the ansatz.
                                  (For VQE this is used directly; for QAOA, the circuit is not used
                                   as a custom ansatz but its depth is used to determine the number of layers.)
        hamiltonian_str (str): The Hamiltonian to be minimized in form of a string.
        method (str): Optimization method. Use 'vqe' for VQE or 'qaoa' for QAOA.
        optimizer: An instance of a classical optimizer (default uses COBYLA).
        maxiter (int): Maximum number of iterations for the optimizer.

    Returns:
        dict: A dictionary with the optimization results including:
              - 'optimal_value': The minimized eigenvalue (energy).
              - 'optimal_parameters': The optimal variational parameters.
              - 'step_count': Total number of optimization steps taken.
              - 'steps': A log of details for each iteration.
              - 'method': Which method was used.
    """
    if method.lower() == "qaoa":
        opt = qml.AdagradOptimizer(stepsize=0.5)

        params = initial_params.copy()
        probs = qaoa_probs_circuit(*params)

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

    elif method.lower() == "vqe":
        seed = 170
        noiseless_estimator = Estimator()
        algorithm = VQE(
            estimator=noiseless_estimator,
            ansatz=ansatz,
            optimizer=optimizer,
            callback=recorder.callback,
            initial_point=initial_params,
        )
    else:
        raise ValueError("Method must be either 'vqe' or 'qaoa'.")

    return {
        "optimal_value": result.eigenvalue.real
        if hasattr(result.eigenvalue, "real")
        else result.eigenvalue,
        "optimal_parameters": result.optimal_point,
        "step_count": recorder.step_count,
        "steps": recorder.steps,
        "method": method.lower(),
    }
