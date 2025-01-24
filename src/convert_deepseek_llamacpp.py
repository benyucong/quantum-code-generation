import pandas as pd
from llama_cpp import Llama  # Use llama-cpp-python for .gguf models
import os
import time

model_path = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")

print(f"Model file exists: {os.path.exists(model_path)}")
print(f"Model file size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")

# Load the CSV file
csv_path = "src/data/benchmark_mapping.csv"
df = pd.read_csv(csv_path, delimiter="|")

# Create output directory
output_dir = "src/data/generated_cirq"
os.makedirs(output_dir, exist_ok=True)

# Path to your local .gguf model
model_path = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"

# Verify the model file
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")

print(f"Model file exists: {os.path.exists(model_path)}")
print(f"Model file size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")

# Load the model using llama-cpp-python
try:
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1,  # Use all available GPU layers
        n_threads=4,      # Adjust based on your CPU cores
        n_ctx=4000,        # Context length
        seed=42,          # For reproducibility
    )
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit(1)

# Define the prompt template
prompt_template = """
Convert the following QASM code to Cirq code:
QASM Code:
{}

Description:
{}

Number of Qubits:
{}
"""

# Iterate over the rows in the DataFrame
for index, row in df.iterrows():
    start = time.time()
    qasm_code = row["QASM"]
    description = row["Description"]
    num_qubits = row["Qubits"]

    # Format the prompt
    prompt = prompt_template.format(qasm_code, description, num_qubits)
    print(f"Generating Cirq code for {row['Algorithm']}", flush=True)

    # Generate the output using the model
    output = llm(
        prompt,
        max_tokens=3000,  # Adjust based on the desired output length
        stop=["QASM Code:", "Description:", "Number of Qubits:"],  # Stop sequences
        temperature=0.6,  # Adjust for creativity (0 = deterministic, 1 = creative)
        top_p=0.9,        # Adjust for diversity
    )

    # Extract the generated Cirq code
    generated_cirq_code = output["choices"][0]["text"]

    # Save the generated code to a file
    output_file = os.path.join(output_dir, f"generated_cirq_{index}.py")
    with open(output_file, "w") as f:
        f.write(generated_cirq_code)

    # Calculate time taken
    time_taken = time.time() - start
    print(f"Generated Cirq code saved to {output_file}. Took {time_taken:.2f} seconds.", flush=True)
