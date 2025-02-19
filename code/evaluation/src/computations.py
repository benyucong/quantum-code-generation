import numpy as np

def compute_measurement_probabilities(sv_array):
    """
    Compute the measurement probabilities from a statevector (as a numpy array).
    """
    probs = np.abs(sv_array)**2
    return probs