import json
import torch
import time
import argparse
import random
from transformers import AutoTokenizer, AutoModelForCausalLM, Gemma3ForCausalLM
from datasets import load_dataset
import os

# Same system prompt for all models. Same as the one used in the training.
SYSTEM_PROMPT = (
    "You are a helpful quantum circuit design assistant. "
    "Provide a quantum circuit in valid QASM 3.0 code with optimal gate parameters so that the output state encodes the solution, ensuring that the measurement outcomes have a high probability of reflecting the correct answer."
)


def create_chat_prompt(tokenizer, sample, is_gemma: bool, few_shot_learning=False):
    n_qubits = sample.get("number_of_qubits")
    n_layers = sample.get("number_of_layers")
    graph = sample.get("graph")
    problem_type = sample.get("problem_type")
    attrs = sample.get("problem_specific_attributes")

    prompt = ""

    if few_shot_learning:
        prompt += (
            "Here are some examples of quantum circuits in QASM 3.0 format:\n"
            "[Example 1] Here is the valid QASM 3.0 code for the Deutsch algorithm with 2 qubits for f(x) = x problem. It is a Hidden Subgroup algorithm. This circuit uses 2 Qubits:\n"
            'OPENQASM 3.0;\ninclude "stdgates.inc";\nbit[2] c;\nqubit[2] q;\nx q[1];\nh q[0];\nh q[1];\ncx q[0], q[1];\nh q[0];\nc[0] = measure q[0];\nc[1] = measure q[1];\n'
            "[Example 2] Here is the valid QASM 3.0 code for the An entangling swapping gate problem. It is a Logical Operation algorithm. This circuit usess 2 Qubits:\n"
            'OPENQASM 3.0;\ninclude "stdgates.inc";\nbit[2] c;\nqubit[2] q;\nx q[0];\ns q[0];\ns q[1];\nh q[0];\ncx q[0], q[1];\nh q[0];\nh q[1];\ncx q[0], q[1];\nh q[0];\nc[0] = measure q[0];\nc[1] = measure q[1];\n'
            "[Example 3] Here is the valid QASM 3.0 code for the vertex cover problem. It is an optimal solution using VQE. This circuit usess 10 Qubits:\n"
            'OPENQASM 3.0;\ninclude "stdgates.inc";\nbit[10] c;\nqubit[10] q;\nrx(1.6013) q[0];\nrz(0.0021) q[0];\nrx(1.5623) q[1];\nrz(0.0019) q[1];\nrx(0.1445) q[2];\nrz(0.0099) q[2];\nrx(0.5475) q[3];\nrz(0.0027) q[3];\nrx(0.1437) q[4];\nrz(0.0093) q[4];\nrx(1.603) q[5];\nrz(0.0035) q[5];\nrx(1.5891) q[6];\nrz(0.0007) q[6];\nrx(1.5999) q[7];\nrz(0.0019) q[7];\nrx(0.1488) q[8];\nrz(0.0052) q[8];\nrx(1.6077) q[9];\nrz(0.0076) q[9];\nc[0] = measure q[0];\nc[1] = measure q[1];\nc[2] = measure q[2];\nc[3] = measure q[3];\nc[4] = measure q[4];\nc[5] = measure q[5];\nc[6] = measure q[6];\nc[7] = measure q[7];\nc[8] = measure q[8];\nc[9] = measure q[9];'
            "[Example 4] Here is the valid QASM 3.0 code for the hypermaxcut problem. It is an optimal solution using QAOA. This circuit uses 7 Qubits:\n"
            'OPENQASM 3.0;\ninclude "stdgates.inc";\nbit[7] c;\nqubit[7] q;\nh q[0];\nh q[1];\nh q[2];\nh q[3];\nh q[4];\nh q[5];\nh q[6];\ncx q[4], q[3];\nrz(-0.0382) q[3];\ncx q[4], q[3];\ncx q[4], q[2];\nrz(-0.0382) q[2];\ncx q[4], q[2];\ncx q[3], q[2];\nrz(-0.0127) q[2];\ncx q[3], q[2];\ncx q[3], q[5];\nrz(-0.0127) q[5];\ncx q[3], q[5];\ncx q[2], q[5];\nrz(-0.0127) q[5];\ncx q[2], q[5];\ncx q[5], q[1];\nrz(-0.0382) q[1];\ncx q[5], q[1];\ncx q[5], q[6];\nrz(-0.0382) q[6];\ncx q[5], q[6];\ncx q[3], q[0];\nrz(-0.0382) q[0];\ncx q[3], q[0];\nrz(0) q[4];\nrz(-0.0127) q[3];\nrz(-0.0127) q[2];\nrz(-0.0127) q[5];\nrz(0) q[1];\nrz(0) q[6];\nrz(0) q[0];\nh q[0];\nrz(0.0764) q[0];\nh q[0];\nh q[1];\nrz(0.0764) q[1];\nh q[1];\nh q[2];\nrz(0.0764) q[2];\nh q[2];\nh q[3];\nrz(0.0764) q[3];\nh q[3];\nh q[4];\nrz(0.0764) q[4];\nh q[4];\nh q[5];\nrz(0.0764) q[5];\nh q[5];\nh q[6];\nrz(0.0764) q[6];\nh q[6];\nc[0] = measure q[0];\nc[1] = measure q[1];\nc[2] = measure q[2];\nc[3] = measure q[3];\nc[4] = measure q[4];\nc[5] = measure q[5];\nc[6] = measure q[6];'
        )

    prompt += (
        f"Your task is to generate a quantum circuit in QASM 3.0 with "
        f"{n_qubits} qubits and {n_layers} layers with optimal parameters that solves the "
        f"{problem_type} {attrs} problem for the following graph: {graph}. "
        "Then ensure that the final answer is correct and in valid QASM 3.0 code."
        "Only return the full QASM code, nothing else."
    )

    if is_gemma:
        chat_template = [
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_PROMPT}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            },
        ]
    else:
        chat_template = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

    return tokenizer.apply_chat_template(
        chat_template,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate quantum circuit outputs for dataset samples"
    )
    parser.add_argument(
        "--uid", type=str, required=True, help="Unique identifier for output file"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to the model checkpoint (or model name)",
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="Dataset to use for generation"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        required=False,
        help="Number of random samples to generate",
    )
    parser.add_argument(
        "--few_shot_learning",
        action="store_true",
        help="Enable few-shot learning examples in the prompt",
    )
    args = parser.parse_args()

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        raise Exception("HW acceleration not available, please run on a GPU.")

    is_gemma = "gemma" in args.model_path

    # Ensure consistent sampling 
    random_seed = 112
    random.seed(random_seed)
    torch.manual_seed(random_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(random_seed)

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)

    if is_gemma:
        model = Gemma3ForCausalLM.from_pretrained(
            args.model_path, 
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        ).to(device)


    generation_length = min(tokenizer.model_max_length, 32000)
    print(f"Running model {args.model_path} with max context length: {generation_length}. \n")
    dataset = load_dataset(args.dataset, split="test")
    dataset_size = len(dataset)
    if args.n_samples is not None and args.n_samples < dataset_size:
        indices = random.sample(range(dataset_size), args.n_samples)
        dataset = dataset.select(indices)
        print(
            f"Randomly selected {args.n_samples} samples from the dataset (original size: {dataset_size})."
        )
    else:
        print(f"Processing entire dataset with {dataset_size} samples.")

    results = []

    for idx, sample in enumerate(dataset):
        inputs = create_chat_prompt(
            tokenizer, sample, is_gemma, few_shot_learning=args.few_shot_learning
        ).to(device)

        start_time = time.time()
        outputs = model.generate(
            **inputs,
            max_length=generation_length,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
        generation_time = time.time() - start_time
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        assistant_indicator = "OPENQASM 3.0;"
        loc_ans = generated_text.rfind(assistant_indicator)
        if loc_ans != -1:
            generated_circuit = generated_text[loc_ans:].strip()
        else:
            generated_circuit = generated_text

        sample_result = {
            "signature": sample.get("signature"),
            "model_name": args.model_path,
            "sample_index": idx,
            "dataset_metrics": {
                "n_qubits": sample.get("number_of_qubits"),
                "n_layers": sample.get("number_of_layers"),
                "graph": sample.get("graph"),
                "optimization_type": sample.get("optimization_type"),
                "problem_type": sample.get("problem_type"),
                "problem_specific_attributes": sample.get(
                    "problem_specific_attributes"
                ),
                "optimal_circuit": sample.get("circuit_with_params"),
                "cost_hamiltonian": sample.get("cost_hamiltonian"),
                "solution": sample.get("solution"),
                "exact_solution": sample.get("exact_solution"),
            },
            "generated_circuit": generated_circuit,
            "generation_time_seconds": generation_time,
        }

        results.append(sample_result)
        print(f"Processed sample {idx} (generation took {generation_time:.2f} seconds)")

    model_name_out = args.model_path.split("/")[-1]
    few_shot = "_few_shot" if args.few_shot_learning else ""
    output_file_name = f"out/quantum_circuits_output_{args.uid}_{model_name_out}{few_shot}.json"
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    with open(output_file_name, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Job finished. Results saved to {output_file_name}")


if __name__ == "__main__":
    main()
