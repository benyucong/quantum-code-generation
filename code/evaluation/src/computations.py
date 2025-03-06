import numpy as np


def compute_measurement_probabilities(sv_array):
    """
    Compute the measurement probabilities from a statevector (as a numpy array).
    """
    probs = np.abs(sv_array) ** 2
    return probs


def compute_relative_entropy(p, q, epsilon=1e-12) -> float:
    """
    Compute the relative entropy (KL divergence) between two probability distributions.
    
    The KL divergence is defined as:
        KL(p || q) = sum( p[i] * (log(p[i]) - log(q[i])) )
    
    Args:
        p (array-like): The first probability distribution (e.g., the expected probabilities).
        q (array-like): The second probability distribution (e.g., the simulated probabilities).
        epsilon (float): A small constant added to q to avoid division by zero.
        
    Returns:
        float: The KL divergence between distributions p and q.
    """
    p = np.array(p, dtype=float)
    q = np.array(q, dtype=float)
    
    # Add epsilon to q to avoid zero probabilities in the logarithm
    q = q + epsilon
    
    # Compute the KL divergence
    kl_divergence = np.sum(p * (np.log(p) - np.log(q)))
    return float(kl_divergence)
