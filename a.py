import pandas as pd

a = pd.read_csv("src/data/benchmark_mapping_with_cirq.csv", delimiter="|")

print(a["cirq"][0])




