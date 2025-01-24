#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --output=out_h100.out
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu-a100-80g

module purge
module load gcc cuda cmake openmpi
module load scicomp-python-env/2024-01
module load scicomp-llm-env

source /scratch/work/jernl1/quantum-code-generation/.venv/bin/activate

export CMAKE_ARGS="-DLLAMA_NO_AVX=ON -DLLAMA_NO_AVX2=ON -DLLAMA_NO_AVX512=ON -DCMAKE_C_COMPILER=$(which gcc) -DCMAKE_CXX_COMPILER=$(which g++)"
pip install --verbose --no-cache-dir llama-cpp-python

python3 -u src/convert_deepseek_llamacpp.py