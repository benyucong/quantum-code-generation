import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import torch
import time

# Load the CSV file
csv_path = "src/data/benchmark_mapping.csv"
df = pd.read_csv(csv_path, delimiter="|")

# Output directory to save generated Cirq code
output_dir = "src/data/generated_cirq"
os.makedirs(output_dir, exist_ok=True)

# Load the model and tokenizer
model_name = "unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF"
tokenizer = AutoTokenizer.from_pretrained(
    model_name, gguf_file="DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
)
model = AutoModelForCausalLM.from_pretrained(
    model_name, gguf_file="DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
)

if torch.backends.mps.is_available():
    print("Using MPS")
    device = torch.device("mps")
    model.to(device)

# Template for generating the prompt
prompt_template = """
Convert the following QASM code to Cirq code:
QASM Code:
{}

Description:
{}

Number of Qubits:
{}
"""

# Iterate through each row in the CSV
for index, row in df.iterrows():
    start = time.time()
    qasm_code = row["QASM"]
    description = row["Description"]
    num_qubits = row["Qubits"]

    # Generate the prompt
    prompt = prompt_template.format(qasm_code, description, num_qubits)
    print(f"Generating Cirq code for {row['Algorithm']}")
    # Tokenize the prompt
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    if torch.backends.mps.is_available():
        inputs = {key: value.to(device) for key, value in inputs.items()}
    # Generate the output using the model
    outputs = model.generate(**inputs, max_length=512)

    # Decode the generated output
    generated_cirq_code = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Save the generated Cirq code to a file
    output_file = os.path.join(output_dir, f"generated_cirq_{index}.py")

    with open(output_file, "w") as f:
        f.write(generated_cirq_code)

    time_taken = time.time() - start
    print(f"Generated Cirq code saved to {output_file}. Took {time_taken:.2f} seconds.")
