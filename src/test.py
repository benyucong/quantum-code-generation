import pandas as pd
import os

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


def generate_synthetic_code(
    row: pd.Series,
    max_length_: int,
    tokenizer_: (PreTrainedTokenizer | PreTrainedTokenizerFast),
    model_,
) -> str:
    """Generate synthetic code from QASM."""

    messages = (
        f"Generate CirQ code that implements the {row['Algorithm']} algorithm on "
        f"{row['Qubits']} qubits. Here is a more detailed description of the algorithm: "
        f"{row['Description']}. It should replicate this QASM code: {row['QASM']}"
    )

    print(f"Generating from prompt: {messages}", flush=True)

    model_inputs = tokenizer_([messages], return_tensors="pt")
    input_length = model_inputs.input_ids.shape[1]

    generated_ids = model_.generate(**model_inputs, max_new_tokens=max_length_)
    synthetic_code = tokenizer_.batch_decode(
        generated_ids[:, input_length:], skip_special_tokens=True
    )[0]

    print(f"The synthetic code generated: {synthetic_code}", flush=True)

    return synthetic_code


if __name__ == "__main__":
    print("Reading CSV...", flush=True)
    df = get_mapping_table(CIRCUITS_FOLDER_PATH)
    print(f"Loaded {len(df)} rows.", flush=True)

    if "cirq" not in df.columns:
        df["cirq"] = None

    print("Starting loop...", flush=True)
    for idx, row in df.iterrows():
        if pd.notna(row["cirq"]):
            print(f"Row {idx} already processed. Skipping...")
            continue

        cirq_code = generate_synthetic_code(row, 2000, tokenizer, model)

        df.at[idx, "cirq"] = cirq_code

        # Save progress
        df.to_csv("src/data/benchmark_mapping_with_cirq.csv", index=False, sep="|")
        print(f"Row {idx} saved to CSV.", flush=True)

    print("Processing complete!")
