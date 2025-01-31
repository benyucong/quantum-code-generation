import os
from llama_cpp import Llama

MODEL_PATH = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
print(f"Model file exists: {os.path.exists(MODEL_PATH)}")
print(f"Model file size: {os.path.getsize(MODEL_PATH) / (1024 * 1024):.2f} MB")

try:
    llm = Llama(model_path=MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
