from transformers import AutoModelForSequenceClassification, AutoTokenizer
from huggingface_hub import HfApi, login
import os

# ----- USER CONFIGURATION -----
MODEL_DIR = "checkpoints/reward_model"  # Path to your trained model directory
HF_REPO = "Benyucong/qwen3-0.6B-reward-model"  # Replace with your HF repo
# HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # (Optional) HF access token
# --------------------------------

# (Optional) Login via token if not already logged in
# if HF_TOKEN:
#     login(token=HF_TOKEN)

# Load model and tokenizer
print("Loading model and tokenizer...")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

# Push to Hugging Face Hub
print(f"Pushing model to {HF_REPO}...")
model.push_to_hub(HF_REPO)
tokenizer.push_to_hub(HF_REPO)

print("✅ Upload complete!")
