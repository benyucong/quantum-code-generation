import json
import torch
import time
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset

def main():
    parser = argparse.ArgumentParser(description="Generate quantum circuit outputs for dataset samples")
    parser.add_argument("--uid", type=str, required=True, help="Unique identifier for output file")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model checkpoint (or model name)")
    parser.add_argument("--n_samples", type=int, required=False, default=100, help="Amount of samples to generate. Default 100")
    args = parser.parse_args()

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        raise Exception("HW acceleration not available, please run on a GPU.")

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_path).to(device)

    dataset = load_dataset("linuzj/hypergraph-max-cut-quantum_tokenized", split="test")
    results = []

    for idx, sample in enumerate(dataset):
        n_qubits = sample.get("number_of_qubits")
        n_layers = sample.get("number_of_qubits")
        hypergraph = sample.get("hypergraph")
        optimization_type = sample.get("optimization_type")

        optimal_circuit_with_params = sample.get("circuit_with_params")
        
        prompt = (
            f"<|im_start|>user Your task is to generate a quantum circuit in QASM 3.0 with "
            f"{n_qubits} qubits and {n_layers} layers with optimal parameters that solve the "
            f"hypergraph max-cut problem using {optimization_type} for the following hypergraph: {hypergraph}. "
            "Then ensure that the final answer is correct and in valid QASM 3.0 code. <|im_start|>assistant"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        start_time = time.time()
        outputs = model.generate(
            **inputs,
            max_length=6000,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
        generation_time = time.time() - start_time
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        loc_ans = generated_text.rfind("Answer: ")
        if loc_ans != -1:
            generated_circuit = generated_text[loc_ans:]
        else:
            generated_circuit = generated_text

        sample_result = {
            "sample_index": idx,
            "dataset_metrics": {
                "n_qubits": n_qubits,
                "n_layers": n_layers,
                "hypergraph": hypergraph,
                "optimization_type": optimization_type,
                "optimal_circuit": optimal_circuit_with_params,
                "cost_hamiltonian": sample.get("cost_hamiltonian"),
                "vqe_solution": sample.get("vqe_solution"),
                "qaoa_solution": sample.get("qaoa_solution"),
                "exact_solution": sample.get("exact_solution")
            },
            "generated_circuit": generated_circuit,
            "generation_time_seconds": generation_time
        }

        results.append(sample_result)
        print(f"Processed sample {idx} (generation took {generation_time:.2f} seconds)")

        if idx >= args.n_samples:
            break

    output_file_name = f"out/quantum_circuits_output_{args.uid}.json"

    with open(output_file_name, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Job finished. Results saved to {output_file_name}")

if __name__ == "__main__":
    main()
