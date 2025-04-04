#!/bin/bash
#SBATCH --job-name=evaluate_samples_quantum_circuit
#SBATCH --time=02:00:00
#SBATCH --output=../../logs/eval_%A_%a.out
#SBATCH --error=../../logs/eval_%A_%a.err
#SBATCH --cpus-per-task=8
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --mem=100GB

module purge
module load scicomp-python-env/2024-01

source .venv/bin/activate

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"


path="../generation/out/quantum_circuits_output_20250328_173826.json"
out="./out/quantum_ciruits_validated_${uid}_final.json"
summary="./out/quantum_ciruits_summary_${uid}_final.json"

python3 -u src/evaluate_samples.py $path $out $summary

