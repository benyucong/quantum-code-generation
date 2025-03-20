#!/bin/bash
#SBATCH --job-name=grpo_quantum_circuit_gen_multigpu
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=../../logs/grpo_%A_%a.out
#SBATCH --error=../../logs/grpo_%A_%a.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=300GB
#SBATCH --gpus=1
#SBATCH --partition=gpu-h200-141g-short
##SBATCH --partition=gpu-debug
##SBATCH --mail-type=BEGIN
##SBATCH --mail-user=linus.jern@aalto.fi

module purge
# module load gcc cuda cmake openmpi
module load scicomp-python-env
module load scicomp-llm-env

source .venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"

accelerate launch test.py