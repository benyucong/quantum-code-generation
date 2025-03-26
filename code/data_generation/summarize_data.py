import os
import argparse
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

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

    optimization_order = ["VQE", "QAOA", "ADAPTIVE"]
    problem_types = list(problem_counts.keys())
    n_problems = len(problem_types)
    x = np.arange(n_problems)
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, opt in enumerate(optimization_order):
        counts = [problem_counts[p].get(opt, 0) for p in problem_types]
        ax.bar(x + (i - 1) * width, counts, width, label=opt)

    ax.set_xlabel("Problem Type")
    ax.set_ylabel("Number of Files")
    ax.set_title("Number of JSON Files by Problem Type and Optimization Type")
    ax.set_xticks(x)
    ax.set_xticklabels(problem_types, rotation=45)
    ax.legend()

    fig.tight_layout()
    plot_filename = "file_counts.png"
    plt.savefig(plot_filename)
    print(f"Plot saved to {plot_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Count JSON files by problem type and optimization type, and plot the results."
    )
    parser.add_argument("--folder", "-f", type=str, default=".", help="Folder containing JSON files.")
    args = parser.parse_args()
    main(args.folder)
