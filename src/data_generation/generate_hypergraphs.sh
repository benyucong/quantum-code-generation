#!/bin/bash

min_qubits=5
max_qubits=10
layers=1
output_dir="out/"

python3 main.py \
    --hypermaxcut \
    --min_qubits ${min_qubits} \
    --max_qubits ${max_qubits} \
    --layers ${layers} \
    --output_dir ${output_dir}