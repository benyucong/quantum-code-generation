#!/bin/bash
#SBATCH --job-name=grpo_quantum_circuit_gen_multigpu
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --output=../../logs/grpo_%A_%a.out
#SBATCH --error=../../logs/grpo_%A_%a.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=400GB
#SBATCH --gpus=4
#SBATCH --partition=gpu-h200-141g-short
##SBATCH --partition=gpu-debug
##SBATCH --mail-type=BEGIN
##SBATCH --mail-user=linus.jern@aalto.fi

module purge
module load scicomp-python-env
module load scicomp-llm-env

source .venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"

base_model_name="Qwen/Qwen2.5-7B-Instruct"
report_to="wandb"

# Optimizer
optim="adamw_8bit"

# HYPERPARAMS
epochs=10
block_size=16384
max_prompt_length=8000
temperature=0.9
learning_rate=0.00001
max_completion_length=8000
num_generations=2
per_device_train_batch_size=2
gradient_accumulation_steps=4


# SAVING
save_strategy='steps'
save_steps=1000

# LOGGING
logging_strategy="steps"
logging_steps=5
log_completions=true

# EVAL (options=[no, steps, epoch])
evaluation_strategy="no"

CUDA_LAUNCH_BLOCKING=0

accelerate launch \
    --config_file="ds_config.yaml" \
    --mixed_precision="bf16" \
    -- \
    grpo.py \
        --model_name=${base_model_name} \
        --output_dir="data/checkpoints/${uid}" \
        --log_level="info" \
        --max_prompt_length=${max_prompt_length} \
        --max_completion_length=${max_completion_length} \
        --per_device_train_batch_size=${per_device_train_batch_size} \
        --gradient_accumulation_steps=${gradient_accumulation_steps} \
        --num_generations=${num_generations} \
        --temperature=${temperature} \
        --learning_rate=${learning_rate} \
        --block_size=${block_size} \
        --logging_strategy=${logging_strategy} \
        --logging_steps=${logging_steps} \
        --log_completions=${log_completions} \
        --evaluation_strategy=${evaluation_strategy} \
        --num_train_epochs=${epochs} \
        --optim=${optim} \
        --bf16=True \
        --report_to=${report_to}