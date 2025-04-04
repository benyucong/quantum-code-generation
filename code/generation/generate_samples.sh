#!/bin/bash
#SBATCH --job-name=generate_samples_quantum_circuit_gen_singlegpu
#SBATCH --time=04:00:00
#SBATCH --output=../../logs/run_%A_%a.out
#SBATCH --error=../../logs/run_%A_%a.err
#SBATCH --cpus-per-task=3
#SBATCH --mem=20GB
#SBATCH --gpus=1
#SBATCH --partition=gpu-h200-141g-short

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate

pip install --upgrade -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"

models=(
  "Qwen/Qwen2.5-Coder-3B-Instruct"
  "Qwen/Qwen2.5-3B-Instruct"
  "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
  "google/codegemma-7b"
  "google/gemma-3-4b-it"
  "meta-llama/Llama-3.2-3B-Instruct"
  "linuzj/quantum-circuit-qubo-3B"
)

n_samples=10
model_path="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
dataset="linuzj/graph-data-quantum-tokenized_sft"  

python3 -u generate_samples.py \
    --uid=${uid} \
    --model_path=${model_path} \
    --n_samples=${n_samples} \
    --dataset=${dataset} \
    --few_shot_learning

