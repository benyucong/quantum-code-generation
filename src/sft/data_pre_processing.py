import os
import json


def summarize_case(case, index=None, key=None):
    """
    Create a short summary of a JSON object (a case).

    Parameters:
        case (dict): The JSON object to summarize.
        index (int, optional): The index number if cases are in a list.
        key (str, optional): The key if cases are stored in a dict.

    Returns:
        str: A multiline summary string.
    """
    lines = []
    if index is not None:
        lines.append(f"Case {index + 1}:")
    elif key is not None:
        lines.append(f"Case: {key}")

    if not isinstance(case, dict):
        lines.append("  [Case is not a dictionary]")
        return "\n".join(lines)

    # Print some key details if available.
    if "ansatz_id" in case:
        lines.append(f"  Ansatz ID: {case['ansatz_id']}")
    if "number_of_qubits" in case:
        lines.append(f"  Number of Qubits: {case['number_of_qubits']}")
    if "number_of_layers" in case:
        lines.append(f"  Number of Layers: {case['number_of_layers']}")
    if "cost_hamiltonian" in case:
        cost = case["cost_hamiltonian"]
        # Truncate the Hamiltonian string if too long.
        truncated = cost if len(cost) <= 60 else cost[:60] + "..."
        lines.append(f"  Cost Hamiltonian: {truncated}")
    if "exact_solution" in case and isinstance(case["exact_solution"], dict):
        exact = case["exact_solution"]
        lines.append("  Exact Solution:")
        for k, v in exact.items():
            lines.append(f"    {k}: {v}")
    if "vqe_solution" in case and isinstance(case["vqe_solution"], dict):
        vqe = case["vqe_solution"]
        lines.append("  VQE Solution:")
        if "expectation_value" in vqe:
            lines.append(f"    Expectation Value: {vqe['expectation_value']}")
        if "total_optimization_steps" in vqe:
            lines.append(f"    Optimization Steps: {vqe['total_optimization_steps']}")
    if "hypergraph" in case and isinstance(case["hypergraph"], dict):
        hyper = case["hypergraph"]
        if "nodes" in hyper:
            lines.append(f"  Hypergraph Nodes: {len(hyper['nodes'])}")
        if "hyperedges" in hyper:
            lines.append(f"  Hypergraph Hyperedges: {len(hyper['hyperedges'])}")

    return "\n".join(lines)


def main():
    filename = "all_data.json"
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading '{filename}': {e}")
        return

    # Handle both list-of-objects and dict-of-objects cases.
    if isinstance(data, list):
        print(f"Found {len(data)} cases in '{filename}' (list format).")
        for i, case in enumerate(data):
            summary = summarize_case(case, index=i)
            print(summary)
            print("-" * 40)
    elif isinstance(data, dict):
        print(f"Found {len(data)} cases in '{filename}' (dict format).")
        for key, case in data.items():
            summary = summarize_case(case, key=key)
            print(summary)
            print("-" * 40)
    else:
        print("Unexpected JSON format. Expected a list or a dictionary.")


if __name__ == "__main__":
    main()
