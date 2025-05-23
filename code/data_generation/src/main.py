import argparse
import warnings


from src.data_generator import DataGenerator
from src.data_classes import OptimizationProblemType

warnings.filterwarnings("ignore", category=FutureWarning)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Generation.")
    parser.add_argument(
        "--problem",
        type=str,
        required=True,
        choices=list(OptimizationProblemType),
        help=f"Specify the problem to generate data for. Available are: {list(OptimizationProblemType)}",
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
    parser.add_argument('--vqe', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()


    generator = DataGenerator(
        problem=args.problem,
        output_path=args.output_path,
        ansatz_template=args.ansatz_template,
        layers=args.layers,
        vqe=args.vqe,
    )
    generator.generate_data()
