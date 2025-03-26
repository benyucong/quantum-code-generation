import os
import json
import statistics
import matplotlib.pyplot as plt
import numpy as np

def process_folder(folder: str):
    lengths = []
    files_processed = 0

    for filename in os.listdir(folder):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(folder, filename)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        circuit = data.get("circuit_with_params", None)
        if circuit is None:
            continue

        file_length = len(circuit)
        lengths.append(file_length)
        files_processed += 1

    if lengths:
        min_length = min(lengths)
        max_length = max(lengths)
        avg_length = statistics.mean(lengths)
        deciles = statistics.quantiles(lengths, n=10)
        print(f"Processed {files_processed} files.")
        print(f"Minimum length: {min_length}")
        print(f"Maximum length: {max_length}")
        print(f"Average length: {avg_length:.2f}")
        print(f"Deciles: {deciles}")

        plt.figure(figsize=(10, 6))
        n, bins, patches = plt.hist(lengths, bins=20, edgecolor='black', alpha=0.7)
        plt.xlabel("Circuit Length (number of characters)")
        plt.ylabel("Frequency")
        plt.title("Histogram of 'circuit_with_params' Lengths")

        stats_text = (
            f"Files processed: {files_processed}\n"
            f"Min: {min_length}\n"
            f"Max: {max_length}\n"
            f"Avg: {avg_length:.2f}\n"
            f"Deciles: " + ", ".join(f"{d:.0f}" for d in deciles)
        )
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plt.text(0.95, 0.95, stats_text, transform=plt.gca().transAxes,
                 fontsize=10, verticalalignment='top', horizontalalignment='right',
                 bbox=props)

        plt.tight_layout()
        plot_filename = "circuit_lengths_histogram.png"
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        plt.show()
    else:
        print("No valid 'circuit_with_params' entries found.")

def main():
    FOLDER = "out/"
    process_folder(FOLDER)

if __name__ == "__main__":
    main()
