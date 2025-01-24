#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --output=out_h100.out
#SBATCH --cpus-per-task=2
#SBATCH --mem=40GB
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-a100-80g

module load scicomp-python-env/2024-01
module load scicomp-llm-env
module load model-huggingface/all
module load gcc cuda cmake openmpi

source /scratch/work/jernl1/quantum-code-generation/.venv/bin/activate

python3 -u src/convert_deepseek_llamacpp.py
