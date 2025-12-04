import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

print("🚀 Loading model in 8-bit (fits in 8GB GPU)...\n")

# 8-bit quantization config
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)

print("📥 Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    "BioMistral/BioMistral-7B",
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.float16
)
print("✅ Base model loaded!\n")

tokenizer = AutoTokenizer.from_pretrained("BioMistral/BioMistral-7B")
tokenizer.pad_token = tokenizer.eos_token

print("🔧 Loading LoRA adapters...")
model = PeftModel.from_pretrained(base_model, "./agentfoundry-finetuned")
model.eval()
print("✅ Model ready!\n")

print("="*70)
print("🤖 TESTING...")
print("="*70)

prompt = """<s>[INST]
Patient in Mumbai, fever for 3 days, chills, headache.
Likely diagnosis?
[/INST]"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("\n⏳ Generating response...\n")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        temperature=0.7,
        do_sample=True
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
if "[/INST]" in response:
    response = response.split("[/INST]")[-1].strip()

print("💬 Response:")
print("-"*70)
print(response)
print("-"*70)
print("\n✅ SUCCESS! Your model works!")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

print("🚀 Loading model in 8-bit (fits in 8GB GPU)...\n")

# 8-bit quantization config
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)

print("📥 Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    "BioMistral/BioMistral-7B",
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.float16
)
print("✅ Base model loaded!\n")

tokenizer = AutoTokenizer.from_pretrained("BioMistral/BioMistral-7B")
tokenizer.pad_token = tokenizer.eos_token

print("🔧 Loading LoRA adapters...")
model = PeftModel.from_pretrained(base_model, "./agentfoundry-finetuned")
model.eval()
print("✅ Model ready!\n")

print("="*70)
print("🤖 TESTING...")
print("="*70)

prompt = """<s>[INST]
Patient in Mumbai, fever for 3 days, chills, headache.
Likely diagnosis?
[/INST]"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("\n⏳ Generating response...\n")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        temperature=0.7,
        do_sample=True
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
if "[/INST]" in response:
    response = response.split("[/INST]")[-1].strip()

print("💬 Response:")
print("-"*70)
print(response)
print("-"*70)
print("\n✅ SUCCESS! Your model works!")
