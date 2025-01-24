import os
import numpy as np
import pandas as pd

TABLE_FOLDER_PATH = "src/data/raw_tables"
CIRCUIT_FOLDER_PATH = "src/data/circuit_files"


def read_csv_files_to_numpy(folder_path):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv") and "large" not in f and "medium" not in f]
    df_full = pd.DataFrame([])

    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        df_full = pd.concat([df_full, df], axis=0)

    return df_full


def get_qasm_content(row, folder_path):
    """Given a DataFrame row with 'Benchmark' and 'Qubits',
    read the corresponding QASM file content."""
    filename = f"{row['Benchmark']}_n{row['Qubits']}.qasm"
    full_path = os.path.join(folder_path, filename)

    if not os.path.exists(full_path):
        print(f"File: {filename} not found")
        return None

    with open(full_path, "r") as f:
        return f.read()

df = read_csv_files_to_numpy(TABLE_FOLDER_PATH)

df.drop(
    ["Reference", "CNOT", "Gates"],
    axis=1,
    inplace=True,
)

# Make unique row for each (Benchmark, Qubits) pair
df = df.assign(Qubits=df["Qubits"].astype(str).str.split(","))
df = df.explode("Qubits")
df["Qubits"] = df["Qubits"].str.strip().astype(int)


df["QASM"] = df.apply(lambda row: get_qasm_content(row, CIRCUIT_FOLDER_PATH), axis=1)

df.to_csv("src/data/benchmark_mapping.csv", index=False, sep="|")

