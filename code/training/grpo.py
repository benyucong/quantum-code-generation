import os
import trl
import warnings
import logging
import transformers
from datasets import load_dataset, concatenate_datasets, DatasetDict
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from grpo_reward_functions import reward_func3, reward_func2, reward_func1
import torch

warnings.filterwarnings("ignore", category=FutureWarning)
transformers.logging.set_verbosity_info()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@dataclass
class TrainingConfig:
    model_name: str = field(default="Qwen/Qwen2.5-3B-Instruct")
    block_size: int = field(default=10000)
    wandb_project: Optional[str] = field(default="quantum-circuit-generation")
    train_file_path: Optional[str] = field(default="linuzj/graph-data-quantum_tokenized_grpo")
    dagger: bool = field(default=False)

    def __post_init__(self):
        os.environ["WANDB_PROJECT"] = self.wandb_project

def train():
    parser = transformers.HfArgumentParser((TrainingConfig, trl.GRPOConfig))
    config, args = parser.parse_args_into_dataclasses()
    args.report_to = ["wandb"]

    log_config = {**asdict(config), **asdict(args)}
    logging.info("Training config: %s", log_config)

    model_config = trl.ModelConfig(
        model_name_or_path=config.model_name,
        torch_dtype="bfloat16",
        attn_implementation="flash_attention_2",
    )

    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_config.model_name_or_path,
        torch_dtype=model_config.torch_dtype,
    )

    # FIX: Use get_input_embeddings() instead of model.embed_tokens.
    embedding_layer = model.get_input_embeddings()
    if embedding_layer.weight.ndim != 2:
        orig_shape = embedding_layer.weight.shape
        logging.info(f"Reshaping input embeddings from {orig_shape} to 2-D.")
        embedding_layer.weight.data = embedding_layer.weight.data.view(orig_shape[0], -1).to(torch.float32)

    dataset = load_dataset(config.train_file_path)
    tokenizer = transformers.AutoTokenizer.from_pretrained(config.model_name, use_fast=True)
    tokenizer.add_special_tokens({"pad_token": "<|fim_pad_token|>"})

    args.dataset_text_field = "text"
    args.max_seq_length = config.block_size

    trainer = trl.GRPOTrainer(
        model,
        reward_funcs=[reward_func1, reward_func2, reward_func3],
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"] if "test" in dataset else dataset["train"],
        args=args,
    )

    trainer.train()
    trainer.save_model(output_dir=args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    trainer.accelerator.wait_for_everyone()

if __name__ == "__main__":
    train()
