import pandas as pd
from llama_cpp import Llama
import os
import time


MODEL_PATH = "/scratch/work/jernl1/model/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf"
CSV_PATH = "src/data/benchmark_mapping.csv"
OUTPUT_DIR = "src/data/generated_cirq"

def check_gpu_support():
    """Verify if llama-cpp-python was installed with GPU support"""
    try:
        Llama(model_path="", n_gpu_layers=0, verbose=False)
        return True
    except Exception as e:
        if "GPU support is disabled" in str(e):
            return False
        raise

def main():
    print("\n=== Initializing System Checks ===", flush=True)
    if not check_gpu_support():
        print("ERROR: GPU acceleration not available in current installation", flush=True)
        exit(1)
    print("✓ Verified GPU-accelerated installation", flush=True)

    
    # Validate paths
    print("\n=== Validating Resources ===", flush=True)
    if not os.path.exists(MODEL_PATH):
        print(f"✗ Missing model file: {MODEL_PATH}", flush=True)
        exit(1)
    if not os.path.exists(CSV_PATH):
        print(f"✗ Missing dataset: {CSV_PATH}", flush=True)
        exit(1)
    print(f"✓ Model size: {os.path.getsize(MODEL_PATH)//(1024**2)}MB", flush=True)
    print(f"✓ Output directory: {OUTPUT_DIR}", flush=True)

    # Prepare data
    print("\n=== Preparing Dataset ===", flush=True)
    try:
        df = pd.read_csv(CSV_PATH, delimiter="|")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Loaded {len(df)} benchmark circuits", flush=True)
    except Exception as e:
        print(f"Failed to initialize dataset: {str(e)}", flush=True)
        exit(1)

    # Initialize model
    print("\n=== Loading AI Model ===", flush=True)
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=-1,
            n_threads=4,
            n_ctx=4000,
            seed=42,
            verbose=False
        )
        print("✓ Model loaded successfully", flush=True)
    except Exception as e:
        print(f"Model initialization failed: {str(e)}", flush=True)
        exit(1)

    # Generation template
    prompt_template = """Convert the following QASM code to Cirq code:
QASM Code:
{}

Description:
{}

Number of Qubits:
{}"""

    # Processing loop
    print("\n=== Starting Conversions ===", flush=True)
    total_start = time.time()
    processed = 0
     
    for index, row in df.iterrows():
        try:
            iter_start = time.time()
            print(f"\nProcessing {index+1}/{len(df)}: {row['Algorithm']}", flush=True)
            print(f"Qubits: {row['Qubits']}, Desc: {row['Description'][:40]}...", flush=True)

            prompt = prompt_template.format(
                row["QASM"],
                row["Description"],
                row["Qubits"]
            )

            gen_start = time.time()
            result = llm(
                prompt,
                max_tokens=10000,
                stop=["QASM Code:", "Description:", "Number of Qubits:"],
                temperature=0.6,
                top_p=0.9
            )
            
            code = result["choices"][0]["text"]
            gen_time = time.time() - gen_start

            base_name = f"{row['Algorithm']}_n{row['Qubits']}"
            output_path = os.path.join(OUTPUT_DIR, f"{base_name}.py")
            
            counter = 1
            while os.path.exists(output_path):
                output_path = os.path.join(OUTPUT_DIR, f"{base_name}_{counter}.py")
                counter += 1

            with open(output_path, "w") as f:
                f.write(f"# Generated from: {row['Algorithm']}\n")
                f.write(f"# Qubits: {row['Qubits']}\n")
                f.write(code)
            
            print(f"✓ Saved to {os.path.basename(output_path)} ({gen_time:.1f}s)", flush=True)
            processed += 1

            if processed == 1:
                break

        except Exception as e:
            print(f"⚠️ Failed to process {row['Algorithm']}: {str(e)}", flush=True)

    total_time = time.time() - total_start
    print("\n=== Completion Report ===", flush=True)
    print(f"Successfully processed: {processed}/{len(df)} circuits", flush=True)
    print(f"Total time: {total_time//60:.0f}m {total_time%60:.0f}s", flush=True)
    print(f"Average time per circuit: {total_time/len(df):.1f}s", flush=True)

if __name__ == "__main__":
    main()