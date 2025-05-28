from datasets import Dataset
import pandas as pd

# Load your labeled dataset
df = pd.read_csv("out/quantum-circuit-qubo-3B_label_data.csv")

# Format into prompt + completion format
def format_example(row):
    prompt = "Generate a valid quantum circuit."
    response = row["generated_circuit"]
    return {
        "text": f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>",
        "reward": float(row["qasm_valid"])  # reward: -1 or 1
    }

# Apply formatting
formatted_data = [format_example(row) for _, row in df.iterrows()]

# Create a Hugging Face Dataset object
dataset = Dataset.from_list(formatted_data)

# Optional: split into train/test
# dataset = dataset.train_test_split(test_size=0.1)

# Save to disk for later use
dataset.save_to_disk("qasm_reward_dataset")