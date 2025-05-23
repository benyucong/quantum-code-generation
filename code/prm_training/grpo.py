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

def reward_len(completions, **kwargs):
    return [-abs(1000 - len(completion)) for completion in completions]

@dataclass
class TrainingConfig:
    model_name: str = field(default="Qwen/Qwen2.5-3B-Instruct")
    block_size: int = field(default=10000)
    wandb_project: Optional[str] = field(default="quantum-circuit-generation")
    train_file_path: Optional[str] = field(default="linuzj/graph-data-quantum-basic-optimizer_tokenized_grpo")

    def __post_init__(self):
        os.environ["WANDB_PROJECT"] = self.wandb_project

def train():
    parser = transformers.HfArgumentParser((TrainingConfig, trl.GRPOConfig))
    config, args = parser.parse_args_into_dataclasses()

    log_config = {**asdict(config), **asdict(args)}
    logger.info("Training config: %s", log_config)

    dataset = load_dataset(config.train_file_path, split="train")

    trainer = trl.GRPOTrainer(
        config.model_name,
        reward_funcs=[reward_len, format_reward, circuit_compile_reward],
        train_dataset=dataset,
        args=args
    )

    trainer.train()
    trainer.save_model(output_dir=args.output_dir)
    trainer.accelerator.wait_for_everyone()

if __name__ == "__main__":
    train()
