#!/bin/bash
#SBATCH --job-name=generate_samples_quantum_circuit_gen_singlegpu
#SBATCH --time=15:00:00
#SBATCH --output=../../logs/run_%A_%a.out
#SBATCH --error=../../logs/run_%A_%a.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=15GB
#SBATCH --gpus=1
#SBATCH --partition=gpu-a100-80g
#SBATCH --array=0-12

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate
pip install --upgrade -r requirements.txt



n_samples=200


uid="$(date +%Y%m%d_%H%M%S)"
dataset="linuzj/graph-data-quantum-tokenized_sft"

declare -a model_paths=(
  "Qwen/Qwen2.5-Coder-3B-Instruct"
  "Qwen/Qwen2.5-Coder-3B-Instruct"
  "Qwen/Qwen2.5-3B-Instruct"
  "Qwen/Qwen2.5-3B-Instruct"
  "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
  "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
  "google/codegemma-7b-it"
  "google/codegemma-7b-it"
  "google/gemma-3-4b-it"
  "google/gemma-3-4b-it"
  "meta-llama/Llama-3.2-3B-Instruct"
  "meta-llama/Llama-3.2-3B-Instruct"
  "linuzj/quantum-circuit-qubo-3B"
)

declare -a few_shot_flags=(
  "--few_shot_learning"
  ""
  "--few_shot_learning"
  ""
  "--few_shot_learning"
  ""
  "--few_shot_learning"
  ""
  "--few_shot_learning"
  ""
  "--few_shot_learning"
  ""
  ""
)

model_path=${model_paths[$SLURM_ARRAY_TASK_ID]}
few_shot=${few_shot_flags[$SLURM_ARRAY_TASK_ID]}

echo "UID: ${uid}"
echo "Running model: ${model_path}"
if [ -n "${few_shot}" ]; then
  echo "Few-shot learning enabled."
else
  echo "Few-shot learning disabled."
fi

python3 -u generate_samples.py \
    --uid=${uid} \
    --model_path=${model_path} \
    --n_samples=${n_samples} \
    --dataset=${dataset} \
    ${few_shot}
