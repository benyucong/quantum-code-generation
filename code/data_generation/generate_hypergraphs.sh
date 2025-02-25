#!/bin/bash

problem="connected_components"
ansatz=13
layers=1
output_dir="out/"

python3 -m src.main \
    --problem   ${problem} \
    --layers ${layers} \
    --ansatz_template ${ansatz} \
    --output_path="${output_dir}"