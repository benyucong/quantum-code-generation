#!/bin/bash
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

export WANDB_API_KEY=$(cat ~/.wandb_api_key)

pip install -r ../../requirements.txt

python3 -u sft.py \
    --output_dir="data"
