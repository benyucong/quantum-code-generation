#!/bin/bash

min_qubits=5
max_qubits=10
layers=1
output_dir="src/data_generation/out/"

python3 -m src.data_generation.main \
    --hypermaxcut \
    --min_qubits ${min_qubits} \
    --max_qubits ${max_qubits} \
    --layers ${layers} \
    --output_path="${output_dir}"