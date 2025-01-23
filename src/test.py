import pandas as pd
import os

# from transformers import pipeline, Pipeline
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
)

CIRCUITS_FOLDER_PATH = "src/data/benchmark_mapping.csv"

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")


# pipe = pipeline(
#     "text-generation", model="mistralai/Mixtral-8x22B-Instruct-v0.1", trust_remote_code=True, device=0
# )


def get_mapping_table(path: str) -> pd.DataFrame:
    """Read the benchmark mapping table."""
    return pd.read_csv(path, delimiter="|")


df = get_mapping_table(CIRCUITS_FOLDER_PATH)


def generate_synthetic_code(
    row: pd.Series,
    max_length_: int,
    tokenizer_: (PreTrainedTokenizer | PreTrainedTokenizerFast),
    model_,
) -> str:
    """Generate synthetic code from QASM."""

    messages = f"Generate CirQ code that implements the {row['Algorithm']} algorithm on {row['Qubits']} qubits. Here is a more detailed description of the algorithm: {row['Description']}. It should replicate this QASM code: {row['QASM']}"
    
    print(f"Generating from prompt: {messages}", flush=True)

    model_inputs = tokenizer_([messages], return_tensors="pt")
    input_length = model_inputs.input_ids.shape[1]

    generated_ids = model_.generate(**model_inputs, max_new_tokens=512)
    synthetic_code = tokenizer_.batch_decode(
        generated_ids[:, input_length:], skip_special_tokens=True
    )[0]

    # print(f"Generating synthetic code for {row['Algorithm']} on {row['Qubits']} qubits")
    # synthetic_code = pipeline(messages, max_length=max_length)
    # print(synthetic_code[0]["generated_text"], "\n")

    print(synthetic_code, flush=True)

    return synthetic_code

print("Starting loop...", flush=True)

df["cirq"] = df.apply(
    lambda row: generate_synthetic_code(row, 100, tokenizer, model), axis=1
)

df.to_csv("src/data/benchmark_mapping_with_cirq.csv", index=False, sep="|")
print(df.head())
