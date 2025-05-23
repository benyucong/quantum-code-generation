#!/bin/bash
#SBATCH --job-name=sft_quantum_circuit_gen_multigpu
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --output=../../logs/sft_%A_%a.out
#SBATCH --error=../../logs/sft_%A_%a.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=400GB
#SBATCH --gpus=32
#SBATCH --partition=gpu-h200-141g-short
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=cong.yu@aalto.fi
##SBATCH --partition=gpu-debug

module purge
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source .venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r requirements.txt


uid="$(date +%Y%m%d_%H%M%S)"

gpus=6
nodes=1

base_model_name="Qwen/Qwen3-32B"
output_dir_name="Benyucong/quantum-circuit-sft-32B"

epochs=15
block_size=16384
save_strategy='steps'
save_steps=24000


# Only do one batch per GPU to reduce memory footprint. Default is 8
per_device_batch_size=1
gradient_accumulation_steps=1

accelerate launch \
        --use_fsdp \
        --config_file "fsdp_config.yaml" \
        --mixed_precision "bf16" \
        --num_processes ${gpus} \
        --num_machines ${nodes} \
        -- \
        sft.py \
                --model_name=${base_model_name} \
                --output_dir=${output_dir_name} \
                --log_level="info" \
                --block_size=${block_size} \
                --num_train_epochs=${epochs} \
                --per_device_train_batch_size=${per_device_batch_size} \
                --per_device_eval_batch_size=${per_device_batch_size} \
                --gradient_accumulation_steps=${gradient_accumulation_steps} \
                --fsdp="full_shard auto_wrap" \
                --fsdp_config="fsdp_config.json" \
                --bf16=True \
                --save_strategy=${save_strategy} \
                --save_steps=${save_steps} \
                --push_to_hub=True \
                --hub_strategy=all_checkpoints
