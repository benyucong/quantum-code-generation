import os
import json
import glob
import numpy as np
import pandas as pd
from transformers import AutoTokenizer

TABLE_FOLDER_PATH = "qasm_bench"
CIRCUIT_FOLDER_PATH = "circuit_files"

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

def read_csv_files_to_numpy(folder_path):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    df_full = pd.DataFrame([])
    
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        df_full = pd.concat([df_full, df], axis=0)
        
    return df_full

def get_qasm_contents(row, folder_path):
    pattern = os.path.join(folder_path, f"{row['Benchmark']}_n{row['Qubits']}*.qasm")
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        print(f"No files found for pattern: {pattern}")
        return None
    
    contents = []
    for file in matching_files:
        with open(file, "r") as f:
            contents.append(f.read())
    return contents

df = read_csv_files_to_numpy(TABLE_FOLDER_PATH)

df.drop(["Reference", "CNOT", "Gates"], axis=1, inplace=True)

df = df.assign(Qubits=df["Qubits"].astype(str).str.split(","))
df = df.explode("Qubits")
df["Qubits"] = df["Qubits"].str.strip().astype(int)

df["QASM"] = df.apply(lambda row: get_qasm_contents(row, CIRCUIT_FOLDER_PATH), axis=1)

entries = []
for _, row in df.iterrows():
    if not row["QASM"]:
        continue

    
    for qasm_text in row["QASM"]:
        tokenized = tokenizer.encode(qasm_text, add_special_tokens=False)
        token_length = len(tokenized)

        if len(qasm_text) > 6000:
            print(len(qasm_text) /token_length)
            continue

        prompt = (
            f"Generate the valid QASM 3.0 code for the {row['Description']} problem. "
            f"It is a {row['Algorithm']} algorithm. "
            f"Use {row['Qubits']} Qubits."
        )
        entry = {
            "prompt": prompt,
            "qasm": qasm_text
        }
        entries.append(entry)

print(len(entries))

# Write all entries to the JSON file.
with open("benchmark_mapping.json", "w") as json_file:
    json.dump(entries, json_file, indent=2)

print("JSON file 'benchmark_mapping.json' has been created.")
