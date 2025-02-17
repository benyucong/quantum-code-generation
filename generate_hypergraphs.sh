#!/bin/bash

ansatz=13
layers=1
output_dir="src/data_generation/out/"

python3 -m src.data_generation.main \
    --hypermaxcut \
    --layers ${layers} \
    --ansatz_template ${ansatz} \
    --output_path="${output_dir}"