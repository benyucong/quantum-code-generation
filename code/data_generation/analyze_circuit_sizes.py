import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import math
from matplotlib.patches import Patch # For custom legend

# --- Configuration ---
FOLDER = "out/" # Folder containing the JSON files
OUTPUT_FILENAME = "circuit_lengths_boxplot_by_problem.png"

# Resemble the color theme (approximations)
# Using distinguishable colors, inspired by the palette hints
OPTIMIZER_COLORS = {
    'qaoa': '#DAE8FC',      # Blueish
    'vqe': '#FFF2CC',       # Orange/Yellowish
    'adaptive_vqe': '#D5E8D4' # Green
    # Add more if needed, or use a colormap
}
DEFAULT_COLOR = '#bab0ac' # Greyish for unknown types

# Consistent Naming for Legends
OPTIMIZER_NAMES = {
    'qaoa': 'QAOA',
    'vqe': 'VQE',
    'adaptive_vqe': 'Adaptive VQE'
}

# Order for plotting boxes within groups and legend consistency
OPTIMIZATION_ORDER = ['qaoa', 'vqe', 'adaptive_vqe']
# --- End Configuration ---

def process_data(folder: str):
    """Reads data from JSON files and organizes it."""
    data_by_problem = defaultdict(lambda: defaultdict(list))
    files_processed = 0
    total_circuits = 0
    all_lengths = []

    print(f"Processing files in folder: {folder}")
    for filename in os.listdir(folder):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(folder, filename)
        files_processed += 1
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            circuit = data.get("circuit_with_params", None)
            problem_type = data.get("problem_type", "Unknown Problem")
            optimization_type = data.get("optimization_type", "vqe").lower() # Ensure lowercase key

            # Ensure problem type is reasonably formatted for display
            problem_type_display = problem_type.replace("_", " ").title()


            # Skip if no circuit data
            if circuit is None:
                continue

            circuit_length = len(circuit)
            # Use consistent keys ('adaptive_vqe')
            if optimization_type == 'adaptive':
                optimization_type = 'adaptive_vqe'

            # Only include data for optimizers we want to plot
            if optimization_type in OPTIMIZATION_ORDER:
                 data_by_problem[problem_type_display][optimization_type].append(circuit_length)
                 all_lengths.append(circuit_length)
                 total_circuits += 1

        except json.JSONDecodeError:
            print(f"Error reading JSON from {filename}: Invalid format")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Finished processing {files_processed} files.")
    print(f"Found {total_circuits} relevant circuits with length data.")
    if not all_lengths:
        print("No circuit lengths found to plot.")
        return None

    return data_by_problem

def plot_grouped_boxplots(data_by_problem):
    """Generates and saves the grouped box plot."""
    if not data_by_problem:
        return

    # Sort problems alphabetically
    sorted_problems = sorted(data_by_problem.keys())
    num_problems = len(sorted_problems)
    num_optimizers = len(OPTIMIZATION_ORDER)

    # --- Plotting ---
    fig_width = max(10, num_problems * 1.5) # Adjust width based on number of problems
    fig_height = 7
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Calculate positions for the groups of boxes
    group_positions = np.arange(num_problems) * (num_optimizers + 1) # Main positions for problems, +1 for spacing
    box_width = 0.8 # Width of individual boxes

    all_plot_data = []
    all_positions = []
    all_colors = []
    tick_positions = []
    tick_labels = []

    # Prepare data and positions for boxplot function
    for i, problem_type in enumerate(sorted_problems):
        problem_data = data_by_problem[problem_type]
        group_base_pos = group_positions[i]
        tick_positions.append(group_base_pos) # Center tick under the group
        tick_labels.append(problem_type)

        for j, opt_type in enumerate(OPTIMIZATION_ORDER):
            lengths = problem_data.get(opt_type, []) # Get data or empty list
            if lengths: # Only plot if data exists
                # Calculate position for this specific box within the group
                current_pos = group_base_pos + (j - (num_optimizers - 1) / 2.0) * box_width
                all_positions.append(current_pos)
                all_plot_data.append(lengths)
                all_colors.append(OPTIMIZER_COLORS.get(opt_type, DEFAULT_COLOR))


    # Create the box plots all at once
    if all_plot_data:
        bp = ax.boxplot(all_plot_data,
                        positions=all_positions,
                        widths=box_width,
                        patch_artist=True,  # Needed to set fill color
                        showfliers=False,   # Hide outliers for cleaner look (optional)
                        medianprops=dict(color="black")) # Make median line black

        # Apply colors to the boxes
        for patch, color in zip(bp['boxes'], all_colors):
            patch.set_facecolor(color)
            patch.set_edgecolor('black') # Keep black edge

    # --- Aesthetics ---    
    ax.set_ylabel("Circuit Length (Characters)", fontsize=20)

    # Set x-axis ticks and labels
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=18)
    ax.set_xlim(tick_positions[0] - num_optimizers*box_width, tick_positions[-1] + num_optimizers*box_width) # Adjust x-limits

    ax.grid(axis='y', linestyle='--', alpha=0.7) # Horizontal grid lines

    # Create custom legend
    legend_elements = [Patch(facecolor=OPTIMIZER_COLORS[opt], edgecolor='black', label=OPTIMIZER_NAMES[opt])
                       for opt in OPTIMIZATION_ORDER if opt in OPTIMIZER_COLORS]
    ax.legend(handles=legend_elements, title="Optimization Type", fontsize=19, title_fontsize=20, loc='upper right')

    fig.tight_layout()

    # Save the plot
    try:
        plt.savefig(OUTPUT_FILENAME, dpi=800, bbox_inches='tight')
        print(f"\nPlot saved to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"\nError saving plot: {e}")
    plt.show()


def main():
    data = process_data(FOLDER)
    if data:
        plot_grouped_boxplots(data)

if __name__ == "__main__":
    main()