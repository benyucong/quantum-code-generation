#!/bin/bash
#SBATCH --time=00:30:00
#SBATCH --output=train_output.out
#SBATCH --cpus-per-task=2
#SBATCH --mem=40GB
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-a100-80g

module load scicomp-python-env/2024-01
module load scicomp-llm-env
module load model-huggingface/all

python3 src/test_mistral.py
