import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")

prompt = "How many stars in the space?"

model_inputs = tokenizer([prompt], return_tensors="pt")
input_length = model_inputs.input_ids.shape[1]

generated_ids = model.generate(**model_inputs, max_new_tokens=20)
print(tokenizer.batch_decode(generated_ids[:, input_length:], skip_special_tokens=True)[0])
