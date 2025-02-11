from typing import Dict
import re
from datasets import load_dataset
from transformers import AutoTokenizer
from functools import partial

QUERY_TEMPLATE_NOANSWER = """{Question}""".strip()


def preprocess(text):
    if text is None:
        return " "
    text = text.strip()
    text = text.replace(" [title]", ". ")
    text = re.sub("\\[.*?\\]", "", text)
    text = text.replace("  ", " ")
    return text


def process_hypergraph_example(example: Dict) -> Dict:
    n_qubits = example["number_of_qubits"]
    n_layers = example["number_of_layers"]
    hypergraph = example["hypergraph"]
    circuit_with_params = example["circuit_with_params"]
    circuit_with_symbols = example["circuit_with_symbols"]

    question = f"You are a highly intelligent AI assistant specializing in quantum circtuits. Your task is to generate a quantum circuit in QASM 3.0 with {n_qubits} qubits and {n_layers} layers to solve the hypergraph max-cut problem using VQE with the following hypergraph: {hypergraph}. Analyse the problem and understand what's being asked, then evaluate each proposed step in the problem solving process. Then ensure that the final answer is correct and in valid QASM 3.0 code."
    answer = circuit_with_params

    return dict(
        question=question,
        answer=answer,
        circuit_with_params=circuit_with_params,
        circuit_with_symbols=circuit_with_symbols,
    )


def process_example(example: Dict, tokenizer):
    hypergraph_data = process_hypergraph_example(example)
    question = hypergraph_data["question"]
    answer = hypergraph_data["answer"]

    if "Answer:" not in answer:
        answer = "Answer: " + answer

    prompt = QUERY_TEMPLATE_NOANSWER.format(Question=question)

    text = tokenizer.apply_chat_template(
        [
            {"role": "user", "content": prompt},
            {
                "role": "assistant",
                "content": "\n<|im_start|>answer\n" + answer.strip(),
            },
        ],
        tokenize=False,
    )
    return dict(text=text)


def tokenize_examples_for_sft(
    upload_data_path: str, download_data_path: str, num_proc: int
):
    dataset = load_dataset(download_data_path, download_mode="force_redownload")
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
    process_example_map = partial(process_example, tokenizer=tokenizer)

    # If the dataset is a DatasetDict with splits (e.g., "train" and "test"),
    # process each split separately.
    if isinstance(dataset, dict) and "train" in dataset:
        for split in dataset.keys():
            dataset[split] = dataset[split].map(
                process_example_map,
                num_proc=num_proc,
                desc=f"Tokenizing SFT data for {split} split",
            )
    else:
        dataset = dataset.map(
            process_example_map,
            num_proc=num_proc,
            desc="Tokenizing SFT data",
        )

    dataset.push_to_hub(upload_data_path)


if __name__ == "__main__":
    tokenize_examples_for_sft(
        download_data_path="linuzj/hypergraph-max-cut-quantum",
        upload_data_path="linuzj/hypergraph-max-cut-quantum_tokenized",
        num_proc=20,
    )
