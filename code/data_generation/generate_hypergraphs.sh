#!/bin/bash

# Supported problems are: "hypermaxcut", "community_detection", "graph_coloring", "connected_components"
# Supported ansatz templates are: 1 - 19

problem="graph_coloring"
ansatz=13
layers=1
output_dir="out/"

python3 -m src.main \
    --problem   ${problem} \
    --layers ${layers} \
    --ansatz_template ${ansatz} \
    --output_path="${output_dir}"