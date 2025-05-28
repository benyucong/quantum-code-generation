import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from transformers import HfArgumentParser, AutoTokenizer
from datasets import load_dataset
from trl import AutoModelForReward, RewardTrainer, RewardConfig

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScriptArguments(RewardConfig):
    model_name_or_path: str = field(default="Qwen/Qwen3-0.6B")
    dataset_path: str = field(default="../evaluation/qasm_reward_dataset")
    output_dir: str = field(default="./out/reward_model_qasm")
    per_device_train_batch_size: int = field(default=2)
    learning_rate: float = field(default=1e-5)
    num_train_epochs: int = field(default=3)
    reporting_to: Optional[str] = field(default="wandb")  # 👈 Important!
    wandb_project: Optional[str] = field(default="qasm-reward-model")
    max_length: int = field(default=1024)
    def __post_init__(self):
        if self.wandb_project is not None:
            os.environ["WANDB_PROJECT"] = self.wandb_project

def tokenize_function(example, tokenizer, max_length):
    return tokenizer(
        example["text"],
        padding="max_length",
        truncation=True,
        max_length=max_length,
    )

def main():
    parser = HfArgumentParser(ScriptArguments)
    args = parser.parse_args_into_dataclasses()[0]

    logger.info("Arguments: %s", args)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    tokenizer.pad_token = tokenizer.eos_token  # Required by some models

    # Load reward model
    model = AutoModelForReward.from_pretrained(args.model_name_or_path)

    # Load dataset from JSON files in dataset_path
    data_files: Dict[str, str] = {
        "train": os.path.join(args.dataset_path, "train.json"),
        "test": os.path.join(args.dataset_path, "test.json"),
    }

    dataset = load_dataset("json", data_files=data_files)
    logger.info("Dataset loaded: %s", dataset)

    # Tokenize the dataset
    tokenized_dataset = dataset.map(
        lambda x: tokenize_function(x, tokenizer, args.max_length),
        batched=True,
        remove_columns=dataset["train"].column_names,
    )

    # Create RewardTrainer
    trainer = RewardTrainer(
        model=model,
        args=args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=dataset["test"] if "test" in dataset else dataset["train"],
        tokenizer=tokenizer,
    )

    # Start training
    trainer.train()

    # Save final model
    trainer.save_model(args.output_dir)
    logger.info("Model saved to %s", args.output_dir)

if __name__ == "__main__":
    main()
