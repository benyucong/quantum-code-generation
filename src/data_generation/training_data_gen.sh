#!/bin/bash
#SBATCH --job-name=trainingdata_gen_batch
#SBATCH --time=01:00:00
#SBATCH --output=../../logs/hypermaxcut_%A_%a.out
#SBATCH --error=../../logs/hypermaxcut_%A_%a.err
#SBATCH --array=0-2
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --ntasks=1
#SBATCH --mem=10GB
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=linus.jern@aalto.fi

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate
pip install -r requirements.txt

ANSATZ_OPTIONS=("5" "6" "13")
OPTION=${ANSATZ_OPTIONS[$SLURM_ARRAY_TASK_ID]}

echo "Running hypermaxcut with ansatz option ${OPTION}..."

layers=1
output_dir="out/"

python3 -m src.main \
    --hypermaxcut \
    --layers ${layers} \
    --ansatz_template ${OPTION} \
    --output_path="${output_dir}"