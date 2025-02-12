#!/bin/bash
#SBATCH --job-name=sft_quantum_circuit_gen_multigpu
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=3
#SBATCH --output=../../logs/sft_%A_%a.out
#SBATCH --error=../../logs/sft_%A_%a.err
#SBATCH --cpus-per-task=3
#SBATCH --mem=50GB
#SBATCH --gpus=3
#SBATCH --partition=gpu-a100-80g
##SBATCH --partition=gpu-debug

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source ../../.venv/bin/activate

export WANDB_API_KEY=$(cat .wandb_api_key)

pip install -r ../../requirements.txt


uid="$(date +%Y%m%d_%H%M%S)"
epochs=40
block_size=512
save_strategy='steps'
save_steps=6000

torchrun --nnodes=1 \
        --nproc_per_node=$SLURM_NTASKS_PER_NODE \
        sft.py \
        --output_dir="data/checkpoints/${uid}" \
        --num_train_epochs=${epochs} \
        --bf16=True \
        --block_size=${block_size} \
        --save_strategy=${save_strategy} \
        --save_steps=${save_steps} \
        --save_only_model=True \
        --fsdp="full_shard auto_wrap" \
        --fsdp_config="fsdp_config_qwen.json"
