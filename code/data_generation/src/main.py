import argparse
import warnings

from src.hypermaxcut.hypermaxcut_data_generator import HyperMaxCutDataGenerator

from .data_generator import DataGenerator

warnings.filterwarnings("ignore", category=FutureWarning)


def main(
    data_problem: DataGenerator,
    layers: int,
):
    print(f"Number of layers: {layers}")

    data_problem.generate_data()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Generation.")
    parser.add_argument(
        "--hypermaxcut", action="store_true", help="Generate Hyper MaxCut data"
    )
    parser.add_argument(
        "--layers", type=int, required=True, help="Number of layers to be used"
    )
    parser.add_argument(
        "--output_path", type=str, required=False, help="Output path for the data"
    )
    parser.add_argument(
        "--ansatz_template",
        type=int,
        required=False,
        help="Choose one of the available Ansatz templates for VQE",
    )

    args = parser.parse_args()

    # Determine what problem to generate data for
    problem = None
    if args.hypermaxcut:
        problem = HyperMaxCutDataGenerator(
            layers=args.layers,
            ansatz_template=args.ansatz_template,
            output_path=args.output_path,
        )
    else:
        raise ValueError("No problem specified")

    main(problem, args.layers)
