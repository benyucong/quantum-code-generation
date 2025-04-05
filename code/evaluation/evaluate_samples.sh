uid="$(date +%Y%m%d_%H%M%S)"

path="../generation/out/quantum_circuits_output_20250404_143833_codegemma-7b-it_few_shot.json"
model="quantum_circuit"
out_path="./out"

python3 src/evaluate_samples.py $path $out_path $model