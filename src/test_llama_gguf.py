import os
from llama_cpp import Llama

model_path = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
print(f"Model file exists: {os.path.exists(model_path)}")
print(f"Model file size: {os.path.getsize(model_path) / (1024 * 1024):.2f} MB")

try:
    llm = Llama(model_path=model_path)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
