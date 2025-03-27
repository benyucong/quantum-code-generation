#!/bin/bash
#SBATCH --job-name=generate_samples_quantum_circuit_gen_singlegpu
#SBATCH --time=03:00:00
#SBATCH --output=../../logs/run_%A_%a.out
#SBATCH --error=../../logs/run_%A_%a.err
#SBATCH --cpus-per-task=3
#SBATCH --mem=20GB
#SBATCH --gpus=1
#SBATCH --partition=gpu-v100-32g
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=linus.jern@aalto.fi
##SBATCH --partition=gpu-debug

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"

n_samples=10
model_path="linuzj/quantum-circuit-qubo-3B"
dataset="linuzj/graph-data-quantum-tokenized_sft"  

python3 -u generate_samples.py \
    --uid=${uid} \
    --model_path=${model_path} \
    --n_samples=${n_samples} \
    --dataset=${dataset}

