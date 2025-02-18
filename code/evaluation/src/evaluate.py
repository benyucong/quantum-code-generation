import json
import sys

from qiskit import transpile
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator
from qiskit_qasm3_import import parse


def parse_qasm(json_file):
    """
    Parses a QASM string from a JSON file and converts it into a quantum circuit.

    Args:
        json_file (str): The path to the JSON file containing the QASM string.

    Returns:
        QuantumCircuit: The parsed quantum circuit.

    Raises:
        ValueError: If the 'model_output' field is not found in the JSON file.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    qasm_str = data.get("model_output", "")
    if not qasm_str:
        raise ValueError("No 'model_output' field found in JSON.")

    if qasm_str.startswith("Answer:"):
        qasm_str = qasm_str[len("Answer:") :].strip()

    circuit = parse(qasm_str)
    return circuit


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_qasm.py <input_json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    circuit = parse_qasm(json_file=json_file)
    print("Reconstructed Qiskit Circuit:")
    print(circuit.draw())

    simulator = AerSimulator()

    circ = transpile(circuit, simulator)

    result = simulator.run(circ).result()
    counts = result.get_counts(circ)
    print(counts)
    plot_histogram(counts, title="Bell-State counts")


if __name__ == "__main__":
    main()
