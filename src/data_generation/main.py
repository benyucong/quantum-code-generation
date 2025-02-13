import argparse

from data_generation.hypermaxcut.hypermaxcut_data_generator import (
    HyperMaxCutDataGenerator,
)

from .data_generator import DataGenerator


def main(
    problem: DataGenerator,
    min_qubits: int,
    max_qubits: int,
    layers: int,
    output_path: str,
):
    print(f"Minimum qubits: {min_qubits}")
    print(f"Maximum qubits: {max_qubits}")
    print(f"Number of layers: {layers}")

    for n_qubits in range(min_qubits, max_qubits + 1):
        problem.initialize(n_qubits, layers, output_path)
        problem.generate_data()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Generation.")
    parser.add_argument(
        "--hypermaxcut", action="store_true", help="Generate Hyper MaxCut data"
    )
    parser.add_argument(
        "--min_qubits", type=int, required=True, help="Minimum number of qubits"
    )
    parser.add_argument(
        "--max_qubits", type=int, required=True, help="Maximum number of qubits"
    )
    parser.add_argument(
        "--layers", type=int, required=True, help="Number of layers to be used"
    )
    parser.add_argument(
        "--output_path", type=str, required=False, help="Output path for the data"
    )

    args = parser.parse_args()

    # Determine what problem to generate data for
    problem = None
    if args.hypermaxcut:
        problem = HyperMaxCutDataGenerator()
    else:
        raise ValueError("No problem specified")

    main(problem, args.min_qubits, args.max_qubits, args.layers, args.output_path)
