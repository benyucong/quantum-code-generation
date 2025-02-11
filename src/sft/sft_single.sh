#!/bin/bash
#SBATCH --job-name=sft_quantum_circuit_gen_singlegpu
#SBATCH --time=03:00:00
#SBATCH --output=../../logs/sft_%A_%a.out
#SBATCH --error=../../logs/sft_%A_%a.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=50GB
#SBATCH --gres=gpu:a100:1
##SBATCH --partition=gpu-debug

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source ../../.venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r ../../requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"
epochs=5
block_size=256

python3 -u sft.py \
    --output_dir="data/checkpoints/${uid}" \
    --num_train_epochs=${epochs} \
    --bf16=True \
    --block_size=${block_size} \
    --save_only_model=True
