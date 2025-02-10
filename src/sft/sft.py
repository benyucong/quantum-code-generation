import os
from dataclasses import dataclass, field, asdict
from typing import Optional
import trl

import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
from datasets import load_dataset, concatenate_datasets, DatasetDict
import transformers


@dataclass
class TrainingConfig:
    model_name: str = field(default="Qwen/Qwen2.5-3B-Instruct")
    block_size: int = field(default=1024)
    wandb_project: Optional[str] = field(default="quantum-circuit-generation")
    wandb_entity: Optional[str] = field(default="linusjern")
    train_file_path: Optional[str] = field(
        default="linuzj/hypergraph-max-cut-quantum_tokenized"
    )
    dagger: bool = field(default=False)

    def __post_init__(self):
        os.environ["WANDB_PROJECT"] = self.wandb_project
        os.environ["WANDB_ENTITY"] = self.wandb_entity


def train():
    parser = transformers.HfArgumentParser((TrainingConfig, trl.SFTConfig))
    config, args = parser.parse_args_into_dataclasses()

    log_config = {**asdict(config), **asdict(args)}
    logging.info("Training config: %s", log_config)

    # ----- Load Model, Data and Tokenizer -----
    model = transformers.AutoModelForCausalLM.from_pretrained(config.model_name)
    dataset = load_dataset(config.train_file_path)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        config.model_name, use_fast=True
    )

    # ----- Setup Instruction Templates -----
    instruction_template = "<|im_start|>user"
    response_template = "<|im_start|>assistant"
    special_tokens_dict = {"pad_token": "<|fim_pad_token|>"}
    tokenizer.add_special_tokens(special_tokens_dict)

    # Only compute loss over assistant responses
    # Verified that it precisely starts where the thinking tokens start and ends with the first pad token
    # via labels being set to -100
    collator = trl.DataCollatorForCompletionOnlyLM(
        instruction_template=instruction_template,
        response_template=response_template,
        tokenizer=tokenizer,
        mlm=False,
    )

    args.dataset_text_field = "text"
    args.max_seq_length = config.block_size

    # ----- Setup Trainer -----
    trainer = trl.SFTTrainer(
        model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"] if "test" in dataset else dataset["train"],
        args=args,
        data_collator=collator,
    )

    # ----- Train Model -----
    trainer.train()
    trainer.save_model(output_dir=args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    trainer.accelerator.wait_for_everyone()


if __name__ == "__main__":
    train()
