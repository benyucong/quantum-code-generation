#!/bin/bash
#SBATCH --job-name=single_config
#SBATCH --time=01:00:00
#SBATCH --output=../../logs/single_config_%j.out
#SBATCH --error=../../logs/single_config_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16GB

# Problems:
#   "hypermaxcut", "community_detection", "graph_coloring", "connected_components",
#   "kclique", "graph_isomorphism", "hamiltonian_path", "matching", "max_flow", "min_cut", "steiner_tree"
#
# Ansatz templates: 1 - 19


: ${PROBLEM:="hamiltonian_path"}
: ${ANSATZ:="5"}
: ${LAYERS:="1"}
: ${OUTPUT_DIR:="out/"}

echo "Running configuration:"
echo "  Problem: ${PROBLEM}"
echo "  Ansatz Template: ${ANSATZ}"
echo "  Layers: ${LAYERS}"
echo "  Output Directory: ${OUTPUT_DIR}"

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env

source .venv/bin/activate

pip install -r requirements.txt

python3 -u -m src.main \
    --problem ${PROBLEM} \
    --layers ${LAYERS} \
    --ansatz_template ${ANSATZ} \
    --output_path="${OUTPUT_DIR}" \
    --vqe