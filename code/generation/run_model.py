import json
import torch
import time
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM

parser = argparse.ArgumentParser(description="Generate quantum circuit output")
parser.add_argument("--uid", type=str, required=True, help="Unique identifier for output file")
parser.add_argument("--model_path", type=str, required=True, help="Path to the model checkpoint (or model name)")
args = parser.parse_args()


if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    raise Exception("HW acceleration not available, run on with GPU please.")

tokenizer = AutoTokenizer.from_pretrained(args.model_path)

model = AutoModelForCausalLM.from_pretrained(
    args.model_path,
).to(device)

n_qubits = 6
n_layers = 1
hypergraph = { "edges": [ [ 3, 4 ], [ 0, 1, 2, 4, 5 ], [ 0, 1, 2, 3, 5 ] ], "nodes": [ 0, 1, 2, 3, 4, 5 ] }
optimization_type = "qaoa"
optimal_circuit_with_params = """OPENQASM 3.0; include "stdgates.inc"; bit[6] c; qubit[6] q; h q[0]; h q[1]; h q[2]; h q[3]; h q[4]; h q[5]; cx q[1], q[0]; rz(-4.9632) q[0]; cx q[1], q[0]; cx q[2], q[0]; rz(-4.9632) q[0]; cx q[2], q[0]; cx q[3], q[0]; rz(-4.9632) q[0]; cx q[3], q[0]; cx q[5], q[0]; rz(-4.9632) q[0]; cx q[5], q[0]; cx q[2], q[1]; rz(-4.9632) q[1]; cx q[2], q[1]; cx q[3], q[1]; rz(-4.9632) q[1]; cx q[3], q[1]; cx q[5], q[1]; rz(-4.9632) q[1]; cx q[5], q[1]; cx q[3], q[2]; rz(-4.9632) q[2]; cx q[3], q[2]; cx q[5], q[2]; rz(-4.9632) q[2]; cx q[5], q[2]; cx q[5], q[3]; rz(-4.9632) q[3]; cx q[5], q[3]; cx q[3], q[2]; cx q[2], q[1]; cx q[1], q[0]; rz(-4.9632) q[0]; cx q[1], q[0]; cx q[2], q[1]; cx q[3], q[2]; cx q[5], q[2]; cx q[2], q[1]; cx q[1], q[0]; rz(-4.9632) q[0]; cx q[1], q[0]; cx q[2], q[1]; cx q[5], q[2]; cx q[5], q[3]; cx q[3], q[1]; cx q[1], q[0]; rz(-4.9632) q[0]; cx q[1], q[0]; cx q[3], q[1]; cx q[5], q[3]; cx q[5], q[3]; cx q[3], q[2]; cx q[2], q[0]; rz(-4.9632) q[0]; cx q[2], q[0]; cx q[3], q[2]; cx q[5], q[3]; cx q[5], q[3]; cx q[3], q[2]; cx q[2], q[1]; rz(-4.9632) q[1]; cx q[2], q[1]; cx q[3], q[2]; cx q[5], q[3]; h q[0]; rz(-1.564) q[0]; h q[0]; h q[1]; rz(-1.564) q[1]; h q[1]; h q[2]; rz(-1.564) q[2]; h q[2]; h q[3]; rz(-1.564) q[3]; h q[3]; h q[4]; rz(-1.564) q[4]; h q[4]; h q[5]; rz(-1.564) q[5]; h q[5]; c[0] = measure q[0]; c[1] = measure q[1]; c[2] = measure q[2]; c[3] = measure q[3]; c[4] = measure q[4]; c[5] = measure q[5];"""

prompt = f"<|im_start|>user Your task is to generate a quantum circuit in QASM 3.0 with {n_qubits} qubits and {n_layers} layers with optimal parameters that solve the hypergraph max-cut problem using {optimization_type} for the following hypergraph: {hypergraph}. Then ensure that the final answer is correct and in valid QASM 3.0 code. <|im_start|>assistant"

inputs = tokenizer(prompt, return_tensors="pt").to(device)

s = time.time()
outputs = model.generate(
    **inputs,
    max_length=6000,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id,
)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
e = time.time()

loc_ans = generated_text.rfind("Answer: ")

generated_circuit = generated_text[loc_ans:]

print(f"Generation finished, took {e - s} seconds\n")
print("Generated text:\n", generated_text)
print("Generated circuit:\n", generated_circuit)
print("\nOptimal circuit:\n", optimal_circuit_with_params)

save_data = {
    "model_output": generated_circuit,
    "optimal_circuit": optimal_circuit_with_params
}

output_file_name = f"out/quantum_circuits_output_{args.uid}.json" 

with open(output_file_name, "w") as f:
    json.dump(save_data, f, indent=2)
