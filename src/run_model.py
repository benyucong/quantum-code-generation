import json
import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM

checkpoint_to_run = "20250211_221717"
model_path = f"sft/data/checkpoints/{checkpoint_to_run}/"

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    raise Exception("HW acceleration not available, run on with GPU please.")

tokenizer = AutoTokenizer.from_pretrained(model_path)

model = AutoModelForCausalLM.from_pretrained(
    model_path,
).to(device)

n_qubits = 5
n_layers = 1
hypergraph = { "hyperedges": [ [ 8, 1, 6 ], [ 0, 4 ], [ 8, 5 ], [ 9, 3 ], [ 8, 2, 6 ], [ 0, 1, 3 ], [ 9, 5 ], [ 8, 7 ] ], "nodes": [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ] }
optimal_circuit_with_params = """OPENQASM 3.0; include "stdgates.inc"; bit c; qubit q; ry(0.08162342034192142) q; ry(1.0357175995236951) q; ry(1.0981701523417267) q; ry(1.4829968689426933) q; ry(1.5781812023588755) q; ry(1.5680960792643521) q; ry(1.1458237036877752) q; ry(1.706034296633401) q; ry(0.2164006712287794) q; ry(-0.0008254821130755374) q; crz(0.9474685685856054) q, q; crz(-0.525828147682339) q, q; crz(-1.5432074953405754) q, q; crz(-0.3593746745693442) q, q; crz(0.005048945444085927) q, q; crz(0.18438725738259026) q, q; crz(-0.04480752407335737) q, q; crz(-0.05841410185299281) q, q; crz(-0.045864180795975124) q, q; crz(-1.4855903826431844) q, q; ry(-0.0009633314380886882) q; ry(1.0449456761584965) q; ry(1.0567865239547807) q; ry(1.4755741957317778) q; ry(1.562997677873634) q; ry(1.5689973356316607) q; ry(1.1103965722749451) q; ry(1.3566352443334782) q; ry(0.20957192108199565) q; ry(0.0007654617137905634) q; crz(0.009311540368473138) q, q; crz(0.006000680260799149) q, q; crz(0.005897892892696928) q, q; crz(0.005394829695406777) q, q; crz(0.005442733523575166) q, q; crz(0.006226202497266505) q, q; crz(0.0012181585886211373) q, q; crz(0.005514601649531891) q, q; crz(0.0033858014976818006) q, q; crz(0.00912462100680234) q, q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q; c = measure q;"""

prompt = f"You are a highly intelligent AI assistant specializing in quantum circtuits. Your task is to generate a quantum circuit in QASM 3.0 with {n_qubits} qubits and {n_layers} layers to solve the hypergraph max-cut problem using VQE with the following hypergraph: {hypergraph}. Analyse the problem and understand what's being asked, then evaluate each proposed step in the problem solving process. Then ensure that the final answer is correct and in valid QASM 3.0 code."

inputs = tokenizer(prompt, return_tensors="pt").to(device)
s = time.time()
outputs = model.generate(**inputs, max_length=10000)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
e = time.time()

loc_ans = s.rfind("Answer: ")

generated_circuit = generated_text[loc_ans:]

print(f"Generation finished, took {e - s} seconds\n")
print("Generated text:\n", generated_circuit)
print("\nOptimal circuit:\n", optimal_circuit_with_params)

save_data = {
    "model_output": generated_circuit,
    "optimal_circuit": optimal_circuit_with_params
}

output_file_name = f"quantum_circuits_output_{time.time()}.json" 

with open(output_file_name, "w") as f:
    json.dump(save_data, f, indent=2)
