import json
import torch
import time
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM

parser = argparse.ArgumentParser(description="Generate quantum circuit output")
parser.add_argument("--uid", type=str, required=True, help="Unique identifier for output file")
args = parser.parse_args()


checkpoint_to_run = "20250213_172028"
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

n_qubits = 6
n_layers = 1
hypergraph = { "hyperedges": [ [ 0, 2 ], [ 1, 2, 4, 5 ], [ 3, 4 ] ], "nodes": [ 0, 1, 2, 3, 4, 5 ] }
optimal_circuit_with_params = """OPENQASM 3.0; include "stdgates.inc"; bit[6] c; qubit[6] q; rx(1.832405082090844) q[0]; rz(1.354359272904784) q[0]; rx(1.2183095110376847) q[1]; rz(0.7830038547472216) q[1]; rx(0.7517226769660915) q[2]; rz(0.8158672496335403) q[2]; rx(1.8659632449633787) q[3]; rz(1.4742864077045108) q[3]; rx(0.8460527958920688) q[4]; rz(0.901629579495171) q[4]; rx(1.2155631954066957) q[5]; rz(0.786027058128776) q[5]; crz(0.8386655839989673) q[5], q[4]; crz(-0.2748069186421075) q[5], q[3]; crz(0.6067427819148714) q[5], q[2]; crz(0.46499698507871434) q[5], q[1]; crz(-0.27388349749602625) q[5], q[0]; crz(0.46546254050796954) q[4], q[5]; crz(-0.2748069186421075) q[4], q[3]; crz(0.6067427819148714) q[4], q[2]; crz(0.46499698507871434) q[4], q[1]; crz(-0.27388349749602625) q[4], q[0]; crz(0.46546254050796954) q[3], q[5]; crz(0.8386655839989673) q[3], q[4]; crz(0.6067427819148714) q[3], q[2]; crz(0.46499698507871434) q[3], q[1]; crz(-0.27388349749602625) q[3], q[0]; crz(0.46546254050796954) q[2], q[5]; crz(0.8386655839989673) q[2], q[4]; crz(-0.2748069186421075) q[2], q[3]; crz(0.46499698507871434) q[2], q[1]; crz(-0.27388349749602625) q[2], q[0]; crz(0.46546254050796954) q[1], q[5]; crz(0.8386655839989673) q[1], q[4]; crz(-0.2748069186421075) q[1], q[3]; crz(0.6067427819148714) q[1], q[2]; crz(-0.27388349749602625) q[1], q[0]; crz(0.46546254050796954) q[0], q[5]; crz(0.8386655839989673) q[0], q[4]; crz(-0.2748069186421075) q[0], q[3]; crz(0.6067427819148714) q[0], q[2]; crz(0.46499698507871434) q[0], q[1]; rx(1.1486237095734215) q[0]; rz(0.009149707705271985) q[0]; rx(1.0250190399681447) q[1]; rz(0.005777094238781348) q[1]; rx(0.6173254303185262) q[2]; rz(0.007708727559566473) q[2]; rx(1.145069285625006) q[3]; rz(0.004413214697901609) q[3]; rx(0.6190048395094477) q[4]; rz(0.0062116924721491405) q[4]; rx(1.0297387599090322) q[5]; rz(0.004014279491411582) q[5]; c[0] = measure q[0]; c[1] = measure q[1]; c[2] = measure q[2]; c[3] = measure q[3]; c[4] = measure q[4]; c[5] = measure q[5];"""

prompt = f"You are a highly intelligent AI assistant specializing in quantum circtuits. Your task is to generate a quantum circuit in QASM 3.0 with {n_qubits} qubits and {n_layers} layers to solve the hypergraph max-cut problem using VQE with the following hypergraph: {hypergraph}. Analyse the problem and understand what's being asked, then evaluate each proposed step in the problem solving process. Then ensure that the final answer is correct and in valid QASM 3.0 code."

inputs = tokenizer(prompt, return_tensors="pt").to(device)

s = time.time()
outputs = model.generate(
    **inputs,
    # max_length=6000,
    # eos_token_id=tokenizer.eos_token_id
    # do_sample=True,
    # temperature=0.7
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

output_file_name = f"quantum_circuits_output_{args.uid}.json" 

with open(output_file_name, "w") as f:
    json.dump(save_data, f, indent=2)
