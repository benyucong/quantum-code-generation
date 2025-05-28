from ast import List
import json
import sys
from typing import Any, Dict
import csv
import re

from qiskit import QuantumCircuit
from qiskit_qasm3_import import parse

ASSISTANT_START_STRING = "<|im_start|>assistant"
ASSISTANS_END_STRING = "<|im_end|>"


def parse_qasm_from_str(qasm_str: str) -> QuantumCircuit:
    # Check if model has generated something after the circuit. This is noted by ``` and a continuation.
    potential_code_split = qasm_str.split("```")
    potential_code = potential_code_split[0].strip()

    if "OPENQASM 3.0" in potential_code:
        qasm_str = potential_code


    qasm_str = re.sub('`', '', qasm_str)

    if qasm_str.startswith(ASSISTANT_START_STRING):
        qasm_str = qasm_str[
            len(ASSISTANT_START_STRING) : len(qasm_str) - len(ASSISTANS_END_STRING)
        ].strip()

    if "OPENQASM 3.0" not in qasm_str:
        raise ValueError("QASM code does not appear to be QASM 3.0.")

    try:
        circuit = parse(qasm_str)
    except Exception as e:
        raise ValueError(
            f"Failed to parse QASM code. It might be invalid QASM 3.0 code: {e}"
        ) from e

    return circuit


def process_circuits(json_file: str):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for idx, sample in enumerate(data):
        generated_qasm = sample.get("generated_circuit", "")

        # ---- Init new params ----
        sample["qasm_valid"] = -1

        if not generated_qasm:
            sample["parse_error"] = "No 'generated_circuit' field found."
            continue

        # ---- 1) CHECK IF CIRCUIT COMPILES ----
        try:
            circuit: QuantumCircuit = parse_qasm_from_str(generated_qasm)
            sample["qasm_valid"] = 1
            print(f"[INFO] SUCCESS! Compile successful for circuit: {idx}")
        except ValueError as err:
            print(f"[FAIL] Failed to compile circuit: {idx}")

        results.append({
            "generated_circuit": generated_qasm,
            "qasm_valid": sample["qasm_valid"],
        })
        
    return results


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    input_file = sys.argv[1]
    out_path = sys.argv[2]
    model = sys.argv[3]

    label_csv = f"{out_path}/{model}_label_data.csv"
    label_data = process_circuits(input_file)
    # todo: store label_data in a csv file
    with open(label_csv, "w", newline='') as csvfile:
        fieldnames = ['generated_circuit', 'qasm_valid']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        writer.writeheader()
        for row in label_data:
            writer.writerow(row)
    print(f"[INFO] Label data saved to {label_csv}")

if __name__ == "__main__":
    main()