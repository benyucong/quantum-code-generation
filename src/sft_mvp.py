import copy
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

import torch
from datasets import DatasetDict, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    PreTrainedTokenizer,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = "Llama-3.2-1B"
DATA_SET_NAME = "OpenCoder-LLM/opc-sft-stage1"
DATA_SET_NAME_REALUSER_INSTRUCT = "realuser_instruct"
TRAINING_EXAMPLES = 100
IGNORE_INDEX = -100
EOT_TOKEN = "<|eot_id|>"


@dataclass
class CustomTrainingArguments(TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")
    model_max_length: int = field(
        default=512,
        metadata={
            "help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."
        },
    )


@dataclass
class DataCollatorForSupervisedDataset(object):
    """Collate examples for supervised fine-tuning."""

    tokenizer: PreTrainedTokenizer

    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        input_ids, labels = tuple(
            [instance[key] for instance in instances] for key in ("input_ids", "labels")
        )
        input_ids = [torch.tensor(x) for x in input_ids]
        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        labels = [torch.tensor(x) for x in labels]
        labels = torch.nn.utils.rnn.pad_sequence(
            labels, batch_first=True, padding_value=IGNORE_INDEX
        )

        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=input_ids.ne(self.tokenizer.pad_token_id),
        )


def build_instruction_prompt(instruction: str) -> str:
    instruction = f"""
    <|start_header_id|>user<|end_header_id|>

    {instruction}<|eot_id|>
    """
    return instruction


def _tokenize_fn(strings: Sequence[str], tokenizer: PreTrainedTokenizer) -> Dict:
    """Tokenize a list of strings."""
    tokenized_list = [
        tokenizer(
            text,
            return_tensors="pt",
            padding="longest",
            max_length=tokenizer.model_max_length,
        )
        for text in strings
    ]

    input_ids = labels = [tokenized.input_ids[0] for tokenized in tokenized_list]
    input_ids_lens = labels_lens = [
        tokenized.input_ids.ne(tokenizer.pad_token_id).sum().item()
        for tokenized in tokenized_list
    ]

    return dict(
        input_ids=input_ids,
        labels=labels,
        input_ids_lens=input_ids_lens,
        labels_lens=labels_lens,
    )


def preprocess(
    sources: Sequence[str],
    targets: Sequence[str],
    tokenizer: PreTrainedTokenizer,
) -> Dict:
    """Preprocess the data by tokenizing."""
    examples = [s + t for s, t in zip(sources, targets)]
    examples_tokenized = _tokenize_fn(examples, tokenizer)
    sources_tokenized = _tokenize_fn(sources, tokenizer)

    input_ids = examples_tokenized["input_ids"]

    labels = copy.deepcopy(input_ids)
    for label, source_len in zip(labels, sources_tokenized["input_ids_lens"]):
        label[:source_len] = IGNORE_INDEX
    return dict(input_ids=input_ids, labels=labels)


def tokenize(examples: dict, tokenizer: AutoTokenizer):
    sources = [
        build_instruction_prompt(instruction) for instruction in examples["instruction"]
    ]
    targets = [f"{output}\n{EOT_TOKEN}" for output in examples["output"]]
    data_dict = preprocess(sources, targets, tokenizer)
    return data_dict


def load_model(model_name: str):
    # If the model is not already downloaded, download it
    if len(os.listdir(f"../../models/{MODEL_NAME}")) == 0:
        model = AutoModelForCausalLM.from_pretrained(
            f"meta-llama/{model_name}", torch_dtype=torch.bfloat16
        )

        model.save_pretrained(f"../../models/{MODEL_NAME}")

    return AutoModelForCausalLM.from_pretrained(
        f"/Users/linusjern/Uni/Dippa/code/models/{model_name}",
        torch_dtype=torch.bfloat16,
    )


def train():
    tokenizer = AutoTokenizer.from_pretrained(
        f"meta-llama/{MODEL_NAME}",
        model_max_length=512,
        padding_side="right",
        use_fast=True,
        trust_remote_code=True,
    )

    model = load_model(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        model.resize_token_embeddings(len(tokenizer))

    print("PAD Token:", tokenizer.pad_token, tokenizer.pad_token_id)
    print("BOS Token", tokenizer.bos_token, tokenizer.bos_token_id)
    print("EOS Token", tokenizer.eos_token, tokenizer.eos_token_id)

    raw_train_datasets = load_dataset(
        DATA_SET_NAME,
        DATA_SET_NAME_REALUSER_INSTRUCT,
        split=f"train[0:{TRAINING_EXAMPLES}]",
    )

    print(f"[INFO] start tokenize", flush=True)

    train_dataset = raw_train_datasets.map(
        tokenize,
        batched=True,
        batch_size=10,
        num_proc=10,
        remove_columns=raw_train_datasets.column_names,
        desc="Running Encoding",
        fn_kwargs={"tokenizer": tokenizer},
    )

    data_collator = DataCollatorForSupervisedDataset(tokenizer=tokenizer)
    data_module = dict(
        train_dataset=train_dataset, eval_dataset=None, data_collator=data_collator
    )

    training_args = CustomTrainingArguments(
        output_dir="../../output", cache_dir="../../cache"
    )

    trainer = Trainer(
        model=model, tokenizer=tokenizer, args=training_args, **data_module
    )

    trainer.train()
    trainer.save_model(training_args.output_dir)
    trainer.tokenizer.save_pretrained(training_args.output_dir)
    trainer.save_state()


if __name__ == "__main__":
    train()
