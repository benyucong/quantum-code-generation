import os
import argparse
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import math # Import math for ceiling function

# --- Configuration ---
OUTPUT_FILENAME = "file_counts_by_problem_and_optimizer.png"

# Resemble the color theme (approximations)
# Use lowercase keys for easier matching after parsing
OPTIMIZER_COLORS = {
    'qaoa': '#DAE8FC',      # Blueish
    'vqe': '#FFF2CC',       # Orange/Yellowish
    'adaptive': '#D5E8D4', # Green (Assuming 'ADAPTIVE' in filename maps to 'adaptive_vqe' logic)
    # Add more if needed, or use a colormap
}
DEFAULT_COLOR = '#bab0ac' # Greyish for unknown types

# Consistent Naming for Legends (using expected keys from the plotting loop)
OPTIMIZER_NAMES = {
    'QAOA': 'QAOA',
    'VQE': 'VQE',
    'ADAPTIVE': 'Adaptive VQE'
}

# Order for plotting bars and legend consistency
# Must match the keys used in OPTIMIZER_NAMES
OPTIMIZATION_ORDER = ["VQE", "QAOA", "ADAPTIVE"]

# --- End Configuration ---


VALID_OPTIMIZATION_TYPES = set(OPTIMIZATION_ORDER) # Dynamically create from order

def parse_filename(filename: str):
    """Parses filename to extract problem and optimization type."""
    if not filename.endswith(".json"):
        return None, None
    if "_OptimizationType." not in filename:
        # Handle potential files without the specific marker if needed, or skip
        # print(f"Skipping {filename}: Marker '_OptimizationType.' not found.")
        return None, None

    parts = filename.split("_OptimizationType.")
    if len(parts) != 2:
        # print(f"Skipping {filename}: Unexpected format after splitting on marker.")
        return None, None

    problem_type = parts[0]
    second_part = parts[1]
    # Split only on the first underscore after the marker
    sub_parts = second_part.split("_", 1)
    if len(sub_parts) < 1: # Should always have at least one part
         # print(f"Skipping {filename}: Unexpected format after marker.")
        return None, None

    optimization_type = sub_parts[0].upper() # Convert to upper to match VALID_OPTIMIZATION_TYPES

    if optimization_type not in VALID_OPTIMIZATION_TYPES:
        # print(f"Skipping {filename}: Invalid optimization type '{optimization_type}'. Valid types: {VALID_OPTIMIZATION_TYPES}")
        return None, None

    # Capitalize problem type words for display, handle underscores
    problem_type_display = problem_type.replace("_", " ").title()

    return problem_type_display, optimization_type

def main(folder: str):
    """Counts files and generates the plot."""
    problem_counts = defaultdict(lambda: defaultdict(int))
    files_processed = 0
    valid_files_counted = 0

    print(f"Scanning folder: {folder}")
    for filename in os.listdir(folder):
        files_processed += 1
        problem_type, optimization_type = parse_filename(filename)
        if problem_type is not None and optimization_type is not None:
            problem_counts[problem_type][optimization_type] += 1
            valid_files_counted += 1

    print(f"\nProcessed {files_processed} total items in the folder.")
    print(f"Counted {valid_files_counted} valid JSON files matching the naming pattern.")

    if not problem_counts:
        print("\nNo valid files found to plot. Exiting.")
        return

    # Sort problem types alphabetically for consistent plotting order
    problem_types = sorted(list(problem_counts.keys()))
    n_problems = len(problem_types)

    # Print summary counts
    print("\nCounts per Problem Type:")
    for p_type in problem_types:
        opt_dict = problem_counts[p_type]
        total_files = sum(opt_dict.values())
        print(f"'{p_type}': {total_files} total")
        for o_type in OPTIMIZATION_ORDER: # Print in consistent order
             count = opt_dict.get(o_type, 0)
             if count > 0: # Only print if count is non-zero
                print(f"  - {OPTIMIZER_NAMES.get(o_type, o_type)}: {count}")

    # --- Plotting ---
    x = np.arange(n_problems)  # the label locations
    width = 0.25  # the width of the bars, adjusted for 3 bars
    num_bars = len(OPTIMIZATION_ORDER)

    # Adjust figure size based on number of problems
    fig_width = max(10, n_problems * 1.2) # Make wider for more problems
    fig_height = 6
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    for i, opt_key in enumerate(OPTIMIZATION_ORDER):
        # Calculate offset for grouped bars - centers the group around x
        offset = width * (i - (num_bars - 1) / 2.0)
        counts = [problem_counts[p].get(opt_key, 0) for p in problem_types]
        color_key = opt_key.lower() # Use lowercase for color dict lookup
        bar_color = OPTIMIZER_COLORS.get(color_key, DEFAULT_COLOR)
        bar_label = OPTIMIZER_NAMES.get(opt_key, opt_key) # Use consistent names for legend

        rects = ax.bar(x + offset, counts, width, label=bar_label, color=bar_color, edgecolor='black', alpha=0.85)
        ax.bar_label(rects, padding=3, fontsize=10) # Add count labels above bars

    # Add some text for labels, title and axes ticks
    ax.set_ylabel("Count", fontsize=20)
    ax.set_xticks(x)
    ax.set_xticklabels(problem_types, rotation=45, ha="right", fontsize=18) # Use ha='right' for better alignment
    ax.legend(title="Optimization Type", fontsize=19, title_fontsize=20)
    ax.grid(axis='y', linestyle='--', alpha=0.7) # Add horizontal grid lines


    fig.tight_layout() # Adjust layout to prevent labels overlapping

    # Save the plot
    try:
        plt.savefig(OUTPUT_FILENAME, dpi=800, bbox_inches='tight')
        print(f"\nPlot saved to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Count JSON files by problem type and optimization type, and plot the results."
    )
    parser.add_argument("--folder", "-f", type=str, default="out/", help="Folder containing JSON files (default: out/).")
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: Folder '{args.folder}' not found.")
    else:
        main(args.folder)