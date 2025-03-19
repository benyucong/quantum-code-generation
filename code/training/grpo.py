import os
import trl
import warnings
import logging
import transformers
from transformers.utils import logging
from datasets import load_dataset, concatenate_datasets, DatasetDict
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from grpo_reward_functions import probability_distrubution_reward, circuit_compile_reward, format_reward
import torch

warnings.filterwarnings("ignore", category=FutureWarning)
logging.set_verbosity_info()
logger = logging.get_logger("transformers")

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

    log_config = {**asdict(config), **asdict(args)}
    logger.info("Training config: %s", log_config)

    model_config = trl.ModelConfig(
        model_name_or_path=config.model_name,
        torch_dtype="bfloat16",
        attn_implementation="flash_attention_2",
    )

    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_config.model_name_or_path,
        torch_dtype=model_config.torch_dtype,
    )

    dataset = load_dataset(config.train_file_path)
    tokenizer = transformers.AutoTokenizer.from_pretrained(config.model_name, use_fast=True)
    tokenizer.add_special_tokens({"pad_token": "<|fim_pad_token|>"})

    args.max_seq_length = config.block_size

    trainer = trl.GRPOTrainer(
        model,
        reward_funcs=[format_reward, circuit_compile_reward, probability_distrubution_reward],
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
