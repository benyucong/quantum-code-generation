#!/bin/bash
#SBATCH --job-name=evaluate_samples_quantum_circuit
#SBATCH --time=02:00:00
#SBATCH --output=../../logs/eval_%A_%a.out
#SBATCH --error=../../logs/eval_%A_%a.err
#SBATCH --cpus-per-task=3
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --mem=5GB

module purge
module load scicomp-python-env/2024-01

source .venv/bin/activate

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"


path="../generation/out/quantum_circuits_output_20250305_133546.json"
out="./out/quantum_ciruits_validated_${uid}.json"
summary="./out/quantum_ciruits_summary_${uid}.json"

python3 src/evaluate_samples.py $path $out $summary

