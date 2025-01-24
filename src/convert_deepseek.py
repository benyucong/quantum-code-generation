import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import torch
import time

csv_path = "src/data/benchmark_mapping.csv"
df = pd.read_csv(csv_path, delimiter="|")

output_dir = "src/data/generated_cirq"
os.makedirs(output_dir, exist_ok=True)

model_name = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
tokenizer = AutoTokenizer.from_pretrained(model_name, gguf_file="DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf", local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(model_name, gguf_file="DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf", local_files_only=True)

if torch.cuda.is_available():
    device = torch.device("cuda")
    model.to(device)

prompt_template = """
Convert the following QASM code to Cirq code:
QASM Code:
{}

Description:
{}

Number of Qubits:
{}
"""

for index, row in df.iterrows():
    s = time.time()
    qasm_code = row["QASM"]
    description = row["Description"]
    num_qubits = row["Qubits"]

    prompt = prompt_template.format(qasm_code, description, num_qubits)
    print(f"Generating Cirq code for {row['Algorithm']}", flush=True)

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    if torch.cuda.is_available():
        inputs = {key: value.to(device) for key, value in inputs.items()}

    outputs = model.generate(**inputs, max_length=512)

    generated_cirq_code = tokenizer.decode(outputs[0], skip_special_tokens=True)

    output_file = os.path.join(output_dir, f"generated_cirq_{index}.py")
    with open(output_file, "w") as f:
        f.write(generated_cirq_code)

    time_taken = time.time() - start
    print(f"Generated Cirq code saved to {output_file}. Took {time_taken:.2f} seconds.", flush=True)
