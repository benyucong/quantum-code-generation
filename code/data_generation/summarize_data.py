import os
import argparse
from collections import defaultdict

VALID_OPTIMIZATION_TYPES = {"VQE", "QAOA", "ADAPTIVE"}

def parse_filename(filename: str):
    if not filename.endswith(".json"):
        return None, None

    if "_OptimizationType." not in filename:
        return None, None

    parts = filename.split("_OptimizationType.")
    if len(parts) != 2:
        return None, None

    problem_type = parts[0]
    second_part = parts[1]

    sub_parts = second_part.split("_", 1)
    if len(sub_parts) < 2:
        return None, None

    optimization_type = sub_parts[0]
    if optimization_type not in VALID_OPTIMIZATION_TYPES:
        return None, None

    return problem_type, optimization_type

def main(folder: str):
    problem_counts = defaultdict(lambda: defaultdict(int))

    for filename in os.listdir(folder):
        problem_type, optimization_type = parse_filename(filename)
        if problem_type is None or optimization_type is None:
            continue
        problem_counts[problem_type][optimization_type] += 1

    for p_type, opt_dict in problem_counts.items():
        total_files = sum(opt_dict.values())
        print(f"Problem type '{p_type}' has {total_files} total file(s).")
        for o_type, count in opt_dict.items():
            print(f"  - Optimization type '{o_type}': {count} file(s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count JSON files by problem type and optimization type.")
    parser.add_argument(
        "--folder",
        "-f",
        type=str,
        default="."
    )
    args = parser.parse_args()
    main(args.folder)
