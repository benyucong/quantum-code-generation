import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional
import os
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
    model_name: str = field(default="Qwen/Qwen2.5-32B-Instruct")
    block_size: int = field(default=32768)
    wandb_project: Optional[str] = field(default="quantum-circuit-generation")
    wandb_entity: Optional[str] = field(default="hashimoto-group")
    train_file_path: Optional[str] = field(default="simplescaling/s1K_tokenized")
    dagger: bool = field(default=False)

    def __post_init__(self):
        os.environ["WANDB_PROJECT"] = self.wandb_project
        os.environ["WANDB_ENTITY"] = self.wandb_entity


if __name__ == "__main__":
    train()
