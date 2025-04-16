#!/bin/bash
#SBATCH --job-name=evaluate_samples_quantum_circuit
#SBATCH --time=10:00:00
#SBATCH --output=../../logs/eval_%A_%a.out
#SBATCH --error=../../logs/eval_%A_%a.err
#SBATCH --cpus-per-task=12
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --mem=60GB

module purge
module load scicomp-python-env/2024-01

source .venv/bin/activate
pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"
out_path="./out"

EXCLUDE=("quantum_circuits_output_20250328_173826_quantum_circuit_3B_400.json")

for file in ../generation/out/*.json; do
    filename=$(basename "$file")
    skip=false
    for e in "${EXCLUDE[@]}"; do
        if [[ "$filename" == "$e" ]]; then
            skip=true
            break
        fi
    done
    if $skip; then
        echo "Skipping $filename"
        continue
    fi

    # Remove the .json extension and the prefix "quantum_circuits_output_"
    base=$(basename "$file" .json)
    base="${base#quantum_circuits_output_}"
    # Remove the first two underscore-separated fields (date and time) to extract the model name
    model=$(echo "$base" | cut -d'_' -f3-)

    echo "Processing $filename with model: $model"
    python3 -u src/evaluate_samples.py "$file" "$out_path" "$model"
done
