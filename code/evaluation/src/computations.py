import numpy as np


def compute_measurement_probabilities(sv_array):
    """
    Compute the measurement probabilities from a statevector (as a numpy array).
    """
    probs = np.abs(sv_array) ** 2
    return probs


def compute_relative_entropy(sim_probs, expected_solution, epsilon=1e-12) -> float:
    """
    Compute the relative entropy (KL divergence) between the expected probabilities and the simulated
    probabilities for the expected states.
    """
    expected_states = expected_solution.get("states", [])
    expected_probs = np.array(expected_solution.get("probabilities", []), dtype=float)
    sim_probs_for_states = np.array([float(sim_probs[i]) for i in expected_states])

    # Add epsilon to avoid zero
    sim_probs_for_states = sim_probs_for_states + epsilon
    kl_divergence = np.sum(
        expected_probs * (np.log(expected_probs) - np.log(sim_probs_for_states))
    )
    return float(kl_divergence)
