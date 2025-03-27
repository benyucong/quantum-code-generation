#!/bin/bash
#SBATCH --job-name=trainingdata_gen_batch
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/trainingdata_gen_%A_%a.out
#SBATCH --error=../../logs/trainingdata_gen_%A_%a.err
#SBATCH --array=0-119
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

# PROBLEMS=("kclique" "graph_isomorphism" "matching" "max_flow" "steiner_tree" "min_cut")
PROBLEMS=("edge_cover" "vertex_cover")
# PROBLEMS=("kclique" "matching" "min_cut")
ANSATZ_OPTIONS=(1 3 4 5 6 7 9 10 11 12 13 14 15 16 18)
LAYERS=(1 2 3 4)

VQE=true

NUM_PROBLEMS=${#PROBLEMS[@]}
NUM_ANSATZ=${#ANSATZ_OPTIONS[@]}
NUM_LAYERS=${#LAYERS[@]}

if [ "$VQE" = true ]; then
    total_tasks=$((NUM_PROBLEMS * NUM_ANSATZ * NUM_LAYERS))
else
    total_tasks=$((NUM_PROBLEMS * NUM_LAYERS))
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
    PROBLEM_INDEX=$(( TASK_ID / NUM_LAYERS ))
    LAYER_INDEX=$(( TASK_ID % NUM_LAYERS ))

    SELECTED_PROBLEM=${PROBLEMS[$PROBLEM_INDEX]}
    SELECTED_ANSATZ=${ANSATZ_OPTIONS[0]}
    SELECTED_LAYER=${LAYERS[$LAYER_INDEX]}
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
