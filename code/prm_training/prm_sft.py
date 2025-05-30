from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
import pandas as pd

# 1. Load dataset
df = pd.read_csv("../evaluation/out/quantum-circuit-qubo-3B_label_data.csv")

# 2. Format dataset entries
def format_example(row):
    prompt = "Generate a valid quantum circuit."
    response = row["generated_circuit"]
    return {
        "text": f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>",
        "reward": float(row["qasm_valid"])
    }

formatted = [format_example(row) for _, row in df.iterrows()]
dataset = Dataset.from_list(formatted)

# 3. Load tokenizer **and set pad token BEFORE loading model**
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 4. Load model AFTER setting tokenizer's pad token
model = AutoModelForSequenceClassification.from_pretrained(
    "Qwen/Qwen3-0.6B",
    num_labels=1,
    trust_remote_code=True,
)

# 5. Update model config to recognize the padding token id
model.config.pad_token_id = tokenizer.pad_token_id
model.config.problem_type = "regression"

# 6. Resize model embeddings to tokenizer vocab size (to include pad token)
model.resize_token_embeddings(len(tokenizer))

# 7. Preprocessing function
def preprocess(example):
    tokenized = tokenizer(example["text"], truncation=True, padding=True, max_length=512)
    tokenized["labels"] = example["reward"]
    return tokenized

tokenized_dataset = dataset.map(preprocess, batched=False)

# 8. Data collator for dynamic padding
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 9. Training arguments
training_args = TrainingArguments(
    output_dir="checkpoints/reward_model",
    per_device_train_batch_size=8,
    learning_rate=2e-5,
    num_train_epochs=10,
    save_strategy="steps",
    save_steps=1000,
    logging_steps=100,
    bf16=True,
    report_to=["wandb"],
)

# 10. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

# 11. Train!
trainer.train()
model.save_pretrained("checkpoints/reward_model")
tokenizer.save_pretrained("checkpoints/reward_model")