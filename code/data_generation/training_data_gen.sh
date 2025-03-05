#!/bin/bash
#SBATCH --job-name=trainingdata_gen_batch
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/trainingdata_gen_%A_%a.out
#SBATCH --error=../../logs/trainingdata_gen_%A_%a.err
#SBATCH --array=0-63
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

# Add JAX configuration
# export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false --xla_force_host_platform_device_count=1"
export JAX_PLATFORM_NAME="cpu"
export JAX_ENABLE_X64=true
export OMP_NUM_THREADS=4

PROBLEMS=("community_detection" "graph_coloring" "connected_components" "hypermaxcut")
ANSATZ_OPTIONS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16)

# Get counts
NUM_ANSATZ=${#ANSATZ_OPTIONS[@]}   # 16
NUM_PROBLEMS=${#PROBLEMS[@]}       # 4

PROBLEM_INDEX=$(( SLURM_ARRAY_TASK_ID / NUM_ANSATZ ))
ANSATZ_INDEX=$(( SLURM_ARRAY_TASK_ID % NUM_ANSATZ ))

SELECTED_PROBLEM=${PROBLEMS[$PROBLEM_INDEX]}
SELECTED_ANSATZ=${ANSATZ_OPTIONS[$ANSATZ_INDEX]}

echo "Running ${SELECTED_PROBLEM} with ansatz option ${SELECTED_ANSATZ}..."

layers=1
output_dir="out/"

python3 -u -m src.main \
    --problem ${SELECTED_PROBLEM} \
    --layers ${layers} \
    --ansatz_template ${SELECTED_ANSATZ} \
    --output_path="${output_dir}"
    
