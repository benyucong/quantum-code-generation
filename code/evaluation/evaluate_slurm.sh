#!/bin/bash
#SBATCH --job-name=evaluate_samples_quantum_circuit
#SBATCH --time=02:00:00
#SBATCH --output=../../logs/eval_%A_%a.out
#SBATCH --error=../../logs/eval_%A_%a.err
#SBATCH --cpus-per-task=6
#SBATCH --nodes=1 
#SBATCH --ntasks=1
#SBATCH --mem=50GB

module purge
module load scicomp-python-env/2024-01

source .venv/bin/activate

pip install -r requirements.txt

uid="$(date +%Y%m%d_%H%M%S)"


path="../generation/out/quantum_circuits_output_20250404_121649_quantum-circuit-qubo-3B.json"
model="quantum-circuit-qubo-3B"
out_path="./out"

python3 -u src/evaluate_samples.py $path $out_path $model

