import os
import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from datasets import Dataset, DatasetDict
from huggingface_hub import login


def preprocess(text):
    """
    Preprocess a text string by removing unwanted characters.
    """
    if text is None:
        return " "
    text = text.strip()
    text = text.replace(" [title]", ". ")
    text = text.replace("  ", " ")
    return text


@dataclass
class QuantumCase:
    signature: str
    problem_type: str
    optimization_type: str
    graph: Dict
    cost_hamiltonian: Optional[str] = None
    ansatz_id: Optional[int] = None
    number_of_qubits: Optional[int] = None
    number_of_layers: Optional[int] = None
    exact_solution: Optional[Dict[str, Any]] = field(default_factory=dict)
    solution: Dict
    circuit_with_params: Optional[str] = None
    circuit_with_symbols: Optional[str] = None
    problem_specific_attributes: Optional[Dict] = field(default_factory=dict)
    adaptive_process: Optional[Dict] = field(default_factory=dict)

    def preprocess(self):
        """
        Preprocess the text fields of the instance.
        """
        if self.cost_hamiltonian:
            self.cost_hamiltonian = preprocess(self.cost_hamiltonian)
        if self.circuit_with_params:
            self.circuit_with_params = preprocess(self.circuit_with_params)
        if self.circuit_with_symbols:
            self.circuit_with_symbols = preprocess(self.circuit_with_symbols)


def load_json_data(filename: str) -> Optional[Any]:
    """
    Load JSON data from the given file.
    """
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading '{filename}': {e}")
        return None


def create_quantum_cases(data: Any) -> List[QuantumCase]:
    """
    Create a list of QuantumCase instances from the JSON data.
    The JSON may be a list or a dict of objects.
    """
    cases: List[QuantumCase] = []

    # If the data is a dict, work with its values.
    if isinstance(data, dict):
        data = data.values()

    for item in data:
        instance = QuantumCase(
            signature=item.get("signature"),
            problem_type=item.get("problem_type"),
            optimization_type=item.get("optimization_type"),
            graph=item.get("hypergraph", {}),
            cost_hamiltonian=item.get("cost_hamiltonian"),
            ansatz_id=item.get("ansatz_id"),
            number_of_qubits=item.get("number_of_qubits"),
            number_of_layers=item.get("number_of_layers"),
            exact_solution=item.get("exact_solution", {}),
            solution=item.get("solution", {}),
            circuit_with_params=item.get("circuit_with_params"),
            circuit_with_symbols=item.get("circuit_with_symbols"),
            problem_specific_attributes=item.get("problem_specific_attributes", {}),
            adaptive_process=item.get("adaptive_process", {}),
        )
        instance.preprocess()
        cases.append(instance)
    return cases


def main():
    filename = "data/all_data.json"
    data = load_json_data(filename)
    if data is None:
        return

    token = os.environ.get("HUGGINGFACE_HUB_TOKEN", "NULL")
    login(token)

    quantum_cases = create_quantum_cases(data)
    print(f"Created {len(quantum_cases)} QuantumCase instances.")

    # Convert the list of dataclass instances into a list of dictionaries.
    records = [asdict(case) for case in quantum_cases]

    # Make Huggingface Dataset
    dataset = Dataset.from_list(records)
    split_dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=42)

    dataset_dict = DatasetDict(
        {"train": split_dataset["train"], "test": split_dataset["test"]}
    )

    # Upload
    repo_id = "linuzj/hypergraph-max-cut-quantum"
    print(f"Uploading dataset to Hugging Face Hub repository '{repo_id}'...")
    try:
        # If you have set your HF token via the CLI or environment variable,
        # you can simply call push_to_hub without a token parameter.
        dataset_dict.push_to_hub(repo_id)
        print("Upload successful!")
    except Exception as e:
        print("Error uploading dataset:", e)


if __name__ == "__main__":
    main()
