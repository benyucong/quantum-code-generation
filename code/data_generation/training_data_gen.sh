#!/bin/bash
#SBATCH --job-name=trainingdata_gen_batch
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/trainingdata_gen_%A_%a.out
#SBATCH --error=../../logs/trainingdata_gen_%A_%a.err
#SBATCH --array=0-71
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=75GB
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=linus.jern@aalto.fi

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env

source .venv/bin/activate
pip install -r requirements.txt

export JAX_PLATFORM_NAME="cpu"
export JAX_ENABLE_X64=true
export OMP_NUM_THREADS=4

PROBLEMS=("community_detection" "graph_coloring" "connected_components" "kclique" "graph_isomorphism" "hamiltonian_path")
# options: ANSATZ_OPTIONS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)
ANSATZ_OPTIONS=(5 12 13 6)
LAYERS=(2 3 4)

VQE=false

NUM_PROBLEMS=${#PROBLEMS[@]}
NUM_ANSATZ=${#ANSATZ_OPTIONS[@]}
NUM_LAYERS=${#LAYERS[@]}

if [ "$VQE" = true ]; then
    total_tasks=$((NUM_PROBLEMS * NUM_ANSATZ * NUM_LAYERS))
else
    total_tasks=$NUM_PROBLEMS
fi

echo "Total tasks expected: $total_tasks"

TASK_ID=${SLURM_ARRAY_TASK_ID}
if [ "$TASK_ID" -ge "$total_tasks" ]; then
    echo "Task ID $TASK_ID is out of range. Exiting."
    exit 0
fi

if [ "$VQE" = true ]; then
    PROBLEM_INDEX=$(( TASK_ID / (NUM_ANSATZ * NUM_LAYERS) ))
    REMAINDER=$(( TASK_ID % (NUM_ANSATZ * NUM_LAYERS) ))
    ANSATZ_INDEX=$(( REMAINDER / NUM_LAYERS ))
    LAYER_INDEX=$(( REMAINDER % NUM_LAYERS ))

    SELECTED_PROBLEM=${PROBLEMS[$PROBLEM_INDEX]}
    SELECTED_ANSATZ=${ANSATZ_OPTIONS[$ANSATZ_INDEX]}
    SELECTED_LAYER=${LAYERS[$LAYER_INDEX]}
else
    SELECTED_PROBLEM=${PROBLEMS[$TASK_ID]}
    SELECTED_ANSATZ=${ANSATZ_OPTIONS[0]}
    SELECTED_LAYER=1
fi

echo "Running ${SELECTED_PROBLEM} | Ansatz ${SELECTED_ANSATZ} | Layers ${SELECTED_LAYER} | VQE=${VQE}"

output_dir="out/"

if [ "$VQE" = true ]; then
    python3 -u -m src.main \
        --problem "${SELECTED_PROBLEM}" \
        --layers "${SELECTED_LAYER}" \
        --ansatz_template "${SELECTED_ANSATZ}" \
        --output_path "${output_dir}" \
        --vqe
else
    python3 -u -m src.main \
        --problem "${SELECTED_PROBLEM}" \
        --layers "${SELECTED_LAYER}" \
        --ansatz_template "${SELECTED_ANSATZ}" \
        --output_path "${output_dir}"
fi
