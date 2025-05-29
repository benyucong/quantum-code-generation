from datasets import load_dataset, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
import pandas as pd

# 1. Load or create dataset
df = pd.read_csv("../evaluation/out/quantum-circuit-qubo-3B_label_data.csv")

# 2. Format the dataset to include "text" and "reward"
def format_example(row):
    prompt = "Generate a valid quantum circuit."
    response = row["generated_circuit"]
    return {
        "text": f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>",
        "reward": float(row["qasm_valid"])  # should be -1.0 or 1.0
    }

formatted = [format_example(row) for _, row in df.iterrows()]
dataset = Dataset.from_list(formatted)

# 3. Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B", trust_remote_code=True)

# 4. Preprocess the data (tokenization + reward as label)
def preprocess(example):
    tokenized = tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)
    tokenized["labels"] = [example["reward"]]  # for regression
    return tokenized

tokenized_dataset = dataset.map(preprocess)

# 5. Load model
model = AutoModelForSequenceClassification.from_pretrained(
    "Qwen/Qwen3-0.6B",
    num_labels=1,  # regression = 1 label
    trust_remote_code=True
)
model.config.problem_type = "regression"

# 6. Training setup
training_args = TrainingArguments(
    output_dir="checkpoints/reward_model",
    per_device_train_batch_size=8,
    learning_rate=2e-5,
    num_train_epochs=3,
    evaluation_strategy="no",
    save_strategy="steps",
    save_steps=1000,
    logging_steps=100,
    bf16=True,  # or fp16=True if on older GPUs
    report_to=["wandb"],  # or ["None"]
)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 7. Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

# 8. Train!
trainer.train()
