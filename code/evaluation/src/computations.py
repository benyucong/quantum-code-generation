import numpy as np
from scipy.stats import entropy


def compute_measurement_probabilities(sv_array):
    """
    Compute the measurement probabilities from a statevector (as a numpy array).
    """
    probs = np.abs(sv_array) ** 2
    return probs


def compute_relative_entropy(p, q, base=2) -> float:
    """
    Compute the relative entropy (KL divergence) using scipy entropy.
    Handles zero cases correctly.
    
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.entropy.html
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)

    kl_div = entropy(pk=p, qk=q, base=base) 
    

    if np.isinf(kl_div):
        return float('inf')
        
    return float(kl_div)
