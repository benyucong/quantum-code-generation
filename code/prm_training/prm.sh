#!/bin/bash
#SBATCH --job-name=prm_sft_singlegpu
#SBATCH --time=05:00:00
#SBATCH --output=../../logs/sft_%A_%a.out
#SBATCH --error=../../logs/sft_%A_%a.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=50GB
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-a100-80g,gpu-h100-80g

module purge
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

python prm_sft.py 
