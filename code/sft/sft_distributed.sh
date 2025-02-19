#!/bin/bash
#SBATCH --job-name=sft_quantum_circuit_gen_multigpu
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --output=../../logs/sft_%A_%a.out
#SBATCH --error=../../logs/sft_%A_%a.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=100GB
#SBATCH --gpus=5
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

base_model_name="Qwen/Qwen2.5-3B-Instruct"

epochs=20
block_size=16384
save_strategy='steps'
save_steps=30000

# Only do one batch per GPU to reduce memory footprint. Default is 8
per_device_batch_size=1
gradient_accumulation_steps=1

torchrun --nnodes=1 \
        --nproc_per_node=$SLURM_NTASKS_PER_NODE \
        --master_port 12345 \
        sft.py \
        --model_name=${base_model_name} \
        --output_dir="data/checkpoints/${uid}" \
        --log_level="info" \
        --block_size=${block_size} \
        --num_train_epochs=${epochs} \
        --per_device_train_batch_size=${per_device_batch_size} \
        --per_device_eval_batch_size=${per_device_batch_size} \
        --gradient_accumulation_steps=${gradient_accumulation_steps} \
        --fsdp="full_shard auto_wrap" \
        --fsdp_config="fsdp_config_qwen.json" \
        --bf16=True \
        --save_strategy=${save_strategy} \
        --save_steps=${save_steps} \
        --save_only_model=True
