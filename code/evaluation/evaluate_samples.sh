uid="$(date +%Y%m%d_%H%M%S)"

path="../generation/out/quantum_circuits_output_20250404_163313_DeepSeek-R1-Distill-Qwen-1.5B_few_shot.json"
model="quantum_circuit"
out_path="./out"

python3 src/evaluate_samples.py $path $out_path $model