#!/bin/bash
#SBATCH --job-name=label
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/eval_%A_%a.out
#SBATCH --error=../../logs/eval_%A_%a.err
#SBATCH --cpus-per-task=6
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --mem=50GB


uid="$(date +%Y%m%d_%H%M%S)"


path="../generation/out/quantum_circuits_output_20250526_150728_quantum-circuit-qubo-3B.json"
out_path="./out"

filename=$(basename "$path")
base="${filename%.json}"
base="${base#quantum_circuits_output_}"
model=$(echo "$base" | cut -d'_' -f3-)

echo "Processing $filename with model: $model"

python3 -u src/label.py $path $out_path $model