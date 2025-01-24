from llama_cpp import Llama

model_path = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
try:
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1,  # Use all available GPU layers
        n_threads=4,      # Adjust based on your CPU cores
        n_ctx=4000,        # Context length
        seed=42,          # For reproducibility
    )
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit(1)

prompt = "Hello, how are you doing? Answer that and also how one would go about finding out about chinese ancient history?"

output = llm(
        prompt,
        max_tokens=2000,
        temperature=0.6,  # Adjust for creativity (0 = deterministic, 1 = creative)
        top_p=0.9,        # Adjust for diversity
    )

print(output)
