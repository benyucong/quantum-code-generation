#!/bin/bash
#SBATCH --job-name=grpo_quantum_circuit_gen_multigpu
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --output=../../logs/grpo_%A_%a.out
#SBATCH --error=../../logs/grpo_%A_%a.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=300GB
#SBATCH --gpus=6
#SBATCH --partition=gpu-h200-141g-short
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=linus.jern@aalto.fi
##SBATCH --partition=gpu-debug

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r requirements.txt


uid="$(date +%Y%m%d_%H%M%S)"

base_model_name="linuzj/quantum-circuit-qubo-3B"
report_to="wandb"

epochs=20
block_size=16384
save_strategy='steps'
save_steps=1000
max_prompt_length=4000
temperature=0.95
learning_rate=0.00001

# Only do one batch per GPU to reduce memory footprint. Default is 8
per_device_batch_size=1
gradient_accumulation_steps=1

accelerate launch --num_processes=$SLURM_NTASKS_PER_NODE --num_machines=1 grpo.py \
        --model_name=${base_model_name} \
        --output_dir="data/checkpoints/${uid}" \
        --log_level="info" \
        --max_prompt_length=${max_prompt_length} \
        --temperature=${temperature} \
        --learning_rate=${learning_rate} \
        --block_size=${block_size} \
        --remove_unused_columns=false \
        --num_train_epochs=${epochs} \
        --per_device_train_batch_size=${per_device_batch_size} \
        --per_device_eval_batch_size=${per_device_batch_size} \
        --gradient_accumulation_steps=${gradient_accumulation_steps} \
        --bf16=True \
        --report_to=${report_to} \
        --save_strategy=${save_strategy} \
        --save_steps=${save_steps} \
        --save_only_model=True
