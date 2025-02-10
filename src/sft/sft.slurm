#!/bin/bash
#SBATCH --time=02:00:00
#SBATCH --output=../../logs/sft.out
#SBATCH --error=../../logs/sft.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-h100-80g

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source ../../.venv/bin/activate

pip install --no-index -r ../../requirements.txt

python3 -u sft.py \
    --output_dir="data"
