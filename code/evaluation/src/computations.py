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
    Compute the relative entropy (KL divergence) using scipy.stats.entropy.
    Handles p[i]=0 and q[i]=0 cases correctly.
    
    Calculates KL(p || q).
    
    Args:
        p (array-like): The first probability distribution (P_sol).
        q (array-like): The second probability distribution (P_gen/P_rand).
        base (float, optional): The logarithmic base to use (e.g., 2 for bits). Defaults to 2.
        
    Returns:
        float: The KL divergence in the specified base.
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)

    # Ensure distributions sum to 1 (optional but good practice)
    # p /= p.sum()
    # q /= q.sum() 
    # Note: Be careful with normalization if epsilon is needed for q=0 cases 
    # where p!=0. Scipy's entropy handles most cases, but extreme care is needed.
    # Let's rely on scipy's internal handling for now.

    # Filter out cases where p[i] == 0, as their contribution is 0
    # Scipy's entropy does this internally.
    
    # Scipy entropy calculates D(p || q) = sum(p_i * log(p_i / q_i))
    # It handles p_i = 0 -> term is 0
    # It handles q_i = 0 (where p_i != 0) -> term is inf (returns inf)
    kl_div = entropy(pk=p, qk=q, base=base) 
    
    # Handle potential inf result if q[i] was 0 where p[i] != 0
    if np.isinf(kl_div):
        # This indicates a fundamental mismatch where the generated distribution
        # assigned zero probability to an outcome the solution considered possible.
        # You might return a very large number, np.inf, or handle as an error/invalid case.
        # Let's return infinity for now as it reflects the math.
        return float('inf')
        
    return float(kl_div)
