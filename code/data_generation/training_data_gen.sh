#!/bin/bash
#SBATCH --job-name=trainingdata_gen_batch
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/trainingdata_gen_%A_%a.out
#SBATCH --error=../../logs/trainingdata_gen_%A_%a.err
#SBATCH --array=0-127
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
pip install custatevec_cu12
pip install pennylane-lightning-gpu

# JAX and OpenMP configuration
export JAX_PLATFORM_NAME="cpu"
export JAX_ENABLE_X64=true
export OMP_NUM_THREADS=4

PROBLEMS=("community_detection" "graph_coloring" "connected_components" "hypermaxcut" "kclique" "graph_isomorphism" "hamiltonian_path" "matching")
ANSATZ_OPTIONS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)

VQE=false

if [ "$VQE" = true ]; then
    total_tasks=$((${#PROBLEMS[@]} * ${#ANSATZ_OPTIONS[@]}))
else
    total_tasks=${#PROBLEMS[@]}
fi

echo "Total tasks expected: $total_tasks"

# Exit if the current task id is out of range. Will happen when VQE is false
if [ "$SLURM_ARRAY_TASK_ID" -ge "$total_tasks" ]; then
    echo "Task ID $SLURM_ARRAY_TASK_ID is out of range (total tasks: $total_tasks). Exiting."
    exit 0
fi

if [ "$VQE" = true ]; then
    NUM_ANSATZ=${#ANSATZ_OPTIONS[@]}
    PROBLEM_INDEX=$(( SLURM_ARRAY_TASK_ID / NUM_ANSATZ ))
    ANSATZ_INDEX=$(( SLURM_ARRAY_TASK_ID % NUM_ANSATZ ))
    SELECTED_PROBLEM=${PROBLEMS[$PROBLEM_INDEX]}
    SELECTED_ANSATZ=${ANSATZ_OPTIONS[$ANSATZ_INDEX]}
else
    SELECTED_PROBLEM=${PROBLEMS[$SLURM_ARRAY_TASK_ID]}
    SELECTED_ANSATZ=${ANSATZ_OPTIONS[0]}
fi

echo "Running ${SELECTED_PROBLEM} with ansatz option ${SELECTED_ANSATZ} (VQE=${VQE})..."

layers=1
output_dir="out/"

python3 -u -m src.main \
    --problem ${SELECTED_PROBLEM} \
    --layers ${layers} \
    --ansatz_template ${SELECTED_ANSATZ} \
    --output_path="${output_dir}" \
    --vqe=${VQE}
