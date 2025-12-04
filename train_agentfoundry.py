# # ============================================
# # IMPORTS - Loading Required Libraries
# # ============================================

# import torch
# # PyTorch: The foundational deep learning library
# # Used for: tensor operations, GPU computation, neural network building blocks

# from transformers import (
#     AutoTokenizer,           # Automatically loads the right tokenizer for any model
#     AutoModelForCausalLM,    # Loads language models designed for text generation
#     BitsAndBytesConfig,      # Configuration for quantization (memory optimization)
#     TrainingArguments        # All hyperparameters for training (batch size, learning rate, etc.)
# )
# # Transformers by HuggingFace: Industry-standard library for LLMs

# from peft import (
#     LoraConfig,                        # Configuration for LoRA (Low-Rank Adaptation)
#     get_peft_model,                    # Wraps your model with LoRA adapters
#     prepare_model_for_kbit_training    # Prepares quantized models for training
# )
# # PEFT: Parameter-Efficient Fine-Tuning library
# # WHY? Fine-tuning 7B parameters would need 28GB VRAM. LoRA fine-tunes only 0.5% of parameters!

# from trl import SFTTrainer
# # TRL: Transformer Reinforcement Learning library
# # SFTTrainer = Supervised Fine-Tuning Trainer (specialized for instruction-following)

# from datasets import load_from_disk
# # Datasets: HuggingFace library for handling data efficiently
# # WHY load_from_disk? We already prepared and saved our dataset earlier


# # ============================================
# # 1. CONFIGURATION - Setting Up Hyperparameters
# # ============================================

# MODEL_NAME = "BioMistral/BioMistral-7B"
# # WHY BioMistral? It's already pre-trained on PubMed medical literature
# # Starting from BioMistral (not base Mistral) gives us a HUGE head start

# OUTPUT_DIR = "./agentfoundry-finetuned"
# # WHERE? This folder will store your trained model
# # It will contain: model weights, tokenizer, training checkpoints

# DATASET_PATH = "./agentfoundry_dataset"
# # WHERE? The dataset you just created with 376,504 examples

# MAX_SEQ_LENGTH = 1024
# # WHAT? Maximum number of tokens (words) per training example
# # WHY 1024? Medical conversations can be long. This allows for detailed Q&A
# # TRADEOFF: Longer = more memory. If you get OOM errors, reduce to 512


# # ============================================
# # 2. LoRA CONFIGURATION - Memory-Efficient Training
# # ============================================

# lora_config = LoraConfig(
#     r=16,
#     # WHAT IS r? LoRA rank - controls how many parameters we actually train
#     # WHY 16? Sweet spot between quality and speed
#     # MATH: Instead of 7B params, we train ~33M (0.5%)
    
#     lora_alpha=32,
#     # WHAT? Scaling factor for LoRA updates
#     # RULE OF THUMB: alpha = 2 * r (so 32 = 2 * 16)
#     # WHY? Controls how much the LoRA adapters influence the model
    
#     lora_dropout=0.05,
#     # WHAT? Regularization technique - randomly drops 5% of connections during training
#     # WHY? Prevents overfitting (model memorizing instead of learning)
    
#     target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
#     # WHAT? Which parts of the transformer we apply LoRA to
#     # q_proj = Query projection (attention mechanism)
#     # k_proj = Key projection
#     # v_proj = Value projection
#     # o_proj = Output projection
#     # WHY THESE? These are the attention layers where most learning happens
#     # TRADEOFF: More modules = better quality but slower training
    
#     bias="none",
#     # WHAT? Whether to train bias parameters
#     # WHY "none"? Saves memory, usually doesn't impact quality much
    
#     task_type="CAUSAL_LM"
#     # WHAT? Type of model we're training
#     # CAUSAL_LM = Causal Language Model (predicts next word)
#     # This is different from MASKED_LM (like BERT) or SEQ_2_SEQ (like T5)
# )


# # ============================================
# # 3. QUANTIZATION CONFIG - Fitting 7B Model in 8GB VRAM
# # ============================================

# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     # WHAT? Load model using 4-bit precision instead of 16-bit
#     # WHY? BioMistral-7B normally needs 14GB VRAM. 4-bit → fits in 7-8GB!
#     # MATH: 7B params * 2 bytes (16-bit) = 14GB
#     #       7B params * 0.5 bytes (4-bit) = 3.5GB (+ overhead = ~7GB)
    
#     bnb_4bit_quant_type="nf4",
#     # WHAT? NormalFloat4 - a special 4-bit format optimized for neural networks
#     # WHY NF4? Better than standard 4-bit (int4) for representing weight distributions
    
#     bnb_4bit_compute_dtype=torch.float16,
#     # WHAT? Use 16-bit for computations (even though weights are 4-bit)
#     # WHY? Balance: 4-bit weights (memory) + 16-bit math (accuracy)
    
#     bnb_4bit_use_double_quant=True
#     # WHAT? Apply quantization to the quantization parameters themselves!
#     # WHY? Saves another ~0.5GB of VRAM
#     # IT'S LIKE: Compressing the compression algorithm
# )


# # ============================================
# # 4. LOAD MODEL & TOKENIZER
# # ============================================

# print("🔧 Loading BioMistral-7B with 4-bit quantization...")

# model = AutoModelForCausalLM.from_pretrained(
#     MODEL_NAME,
#     # Downloads BioMistral-7B from HuggingFace Hub
    
#     quantization_config=bnb_config,
#     # Apply 4-bit quantization during loading
#     # THIS IS KEY: Model is quantized BEFORE loading into memory
    
#     device_map="auto",
#     # WHAT? Automatically distribute model layers across CPU/GPU
#     # WHY? If model doesn't fit in GPU, overflow to RAM
#     # FOR YOU: With RTX 4060 (8GB), everything should fit on GPU
    
#     trust_remote_code=True,
#     # WHAT? Allow execution of custom code from model repository
#     # WHY? Some models have custom architectures
#     # SECURITY NOTE: Only use with trusted models (BioMistral is safe)
    
#     torch_dtype=torch.float16
#     # WHAT? Use 16-bit floating point for non-quantized parts
#     # WHY? Faster than 32-bit, minimal accuracy loss
# )

# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# # TOKENIZER: Converts text → numbers (tokens) that model understands
# # Example: "Patient: I have fever" → [2523, 25, 315, 423, 1891]

# tokenizer.pad_token = tokenizer.eos_token
# # WHAT? Set padding token = end-of-sequence token
# # WHY NEEDED? Not all inputs are same length. Padding fills shorter ones
# # Example: ["Hi"] → ["Hi", <pad>, <pad>] to match longer inputs

# tokenizer.padding_side = "right"
# # WHAT? Add padding tokens to the RIGHT of text
# # WHY? For causal LMs, we predict left-to-right, so right-padding is correct


# # ============================================
# # 5. PREPARE MODEL FOR LoRA TRAINING
# # ============================================

# model = prepare_model_for_kbit_training(model)
# # WHAT DOES THIS DO?
# # 1. Casts LayerNorm layers to float32 (stability)
# # 2. Enables gradient checkpointing (memory optimization)
# # 3. Freezes all base model parameters (only LoRA adapters will train)
# # WHY? Without this, training a quantized model would crash

# model = get_peft_model(model, lora_config)
# # WHAT? Wraps the base model with LoRA adapters
# # BEFORE: 7,241,748,480 parameters (all frozen)
# # AFTER: 7,241,748,480 frozen + 33,554,432 trainable = 7,275,302,912 total
# # BUT we only train 0.46% of them!

# print("✅ Model loaded successfully!")
# print("📊 Trainable parameters:")
# model.print_trainable_parameters()
# # OUTPUT: "trainable params: 33,554,432 || all params: 7,275,302,912 || trainable%: 0.4613"
# # THIS IS THE MAGIC: We're only training 33M parameters instead of 7B!


# # ============================================
# # 6. LOAD DATASET
# # ============================================

# print("\n📚 Loading prepared dataset...")
# dataset = load_from_disk(DATASET_PATH)
# # Loads the 376,504 examples you prepared earlier

# print(f"Training examples: {len(dataset['train'])}")      # 338,853
# print(f"Validation examples: {len(dataset['validation'])}")  # 37,651

# # WHY VALIDATION? To check if model is overfitting
# # OVERFITTING = Memorizing training data instead of learning patterns


# # ============================================
# # 7. TRAINING CONFIGURATION
# # ============================================

# training_args = TrainingArguments(
#     output_dir=OUTPUT_DIR,
#     # WHERE? Save checkpoints here every 200 steps
    
#     per_device_train_batch_size=1,
#     # WHAT? Process 1 example at a time per GPU
#     # WHY SO LOW? Long sequences (1024 tokens) eat memory
#     # FOR COMPARISON: With 512 max_length, you could use batch_size=2
    
#     gradient_accumulation_steps=8,
#     # WHAT? Accumulate gradients over 8 batches before updating
#     # EFFECTIVE BATCH SIZE = 1 * 8 = 8
#     # WHY? Simulates larger batch size without memory overhead
#     # STABILITY: Larger effective batches = more stable training
    
#     num_train_epochs=3,
#     # WHAT? Go through entire dataset 3 times
#     # WHY 3? Standard for fine-tuning. More = overfitting risk
#     # MATH: 338,853 examples * 3 epochs = 1,016,559 total training steps
    
#     learning_rate=2e-4,
#     # WHAT? How much to adjust weights each step
#     # WHY 2e-4 (0.0002)? Standard for LoRA fine-tuning
#     # TOO HIGH (1e-3): Model forgets original knowledge (catastrophic forgetting)
#     # TOO LOW (1e-5): Learning too slow
    
#     fp16=True,
#     # WHAT? Use 16-bit mixed precision training
#     # WHY? 2x faster, uses less memory, minimal accuracy loss
#     # REQUIRES: GPU with Tensor Cores (RTX 4060 ✅ has them)
    
#     logging_steps=10,
#     # WHAT? Print training loss every 10 steps
#     # OUTPUT: "Step 10: loss=1.8234"
#     # WHY? Monitor if training is working (loss should decrease)
    
#     save_steps=200,
#     # WHAT? Save a checkpoint every 200 steps
#     # WHY? If training crashes, you don't lose everything
#     # WHERE? ./agentfoundry-finetuned/checkpoint-200, checkpoint-400, etc.
    
#     save_total_limit=3,
#     # WHAT? Only keep last 3 checkpoints
#     # WHY? Checkpoints are big (3-4GB each). This saves disk space
#     # EXAMPLE: After step 1000, only keep checkpoint-600, -800, -1000
    
#     evaluation_strategy="steps",
#     # WHAT? When to run validation
#     # "steps" = Every eval_steps
#     # Alternative: "epoch" (after each full pass through data)
    
#     eval_steps=200,
#     # WHAT? Run validation every 200 steps
#     # WHY? Check if model is overfitting
#     # OUTPUT: "eval_loss: 0.7234"
    
#     optim="paged_adamw_8bit",
#     # WHAT? Optimizer algorithm
#     # WHY THIS ONE? Adam optimizer but in 8-bit (saves memory)
#     # "paged" = Uses system RAM if GPU memory runs out
#     # STANDARD: AdamW is the best optimizer for transformers
    
#     warmup_steps=100,
#     # WHAT? Gradually increase learning rate for first 100 steps
#     # WHY? Prevents unstable training at start
#     # SCHEDULE: 0 → 2e-4 over 100 steps, then stays at 2e-4
    
#     lr_scheduler_type="cosine",
#     # WHAT? How learning rate changes over training
#     # COSINE: Starts high, smoothly decreases to near-zero
#     # WHY? Models learn coarse patterns first, then fine details
#     # VISUALIZATION: Learning rate follows a cosine curve
    
#     report_to="none",
#     # WHAT? Don't send metrics to tracking services (WandB, TensorBoard)
#     # WHY? Simplifies setup. You can change to "tensorboard" later
    
#     max_grad_norm=0.3,
#     # WHAT? Clip gradients to prevent explosions
#     # WHY? Sometimes gradients get huge → model diverges
#     # 0.3 = If gradient > 0.3, scale it down to 0.3
    
#     weight_decay=0.001
#     # WHAT? L2 regularization penalty
#     # WHY? Prevents weights from getting too large (overfitting)
#     # 0.001 = Very light regularization (standard for fine-tuning)
# )


# # ============================================
# # 8. CREATE TRAINER
# # ============================================

# print("\n🚀 Starting fine-tuning...")
# print("⏰ Expected time: 10-14 hours on RTX 4060")
# print("💡 TIP: Let this run overnight!\n")

# trainer = SFTTrainer(
#     # SFTTrainer = Supervised Fine-Tuning Trainer
#     # Specialized for instruction-following format
    
#     model=model,
#     # Your LoRA-wrapped, quantized BioMistral model
    
#     train_dataset=dataset["train"],
#     # 338,853 training examples
    
#     eval_dataset=dataset["validation"],
#     # 37,651 validation examples
    
#     dataset_text_field="text",
#     # WHAT? Which column in dataset has the text
#     # YOUR DATASET: Each row has {"text": "<s>[INST]...[/INST]..."}
    
#     max_seq_length=MAX_SEQ_LENGTH,
#     # WHAT? Truncate inputs longer than 1024 tokens
#     # WHY NEEDED? Model has fixed context window
    
#     tokenizer=tokenizer,
#     # For converting text → tokens
    
#     args=training_args,
#     # All the hyperparameters we set above
    
#     peft_config=lora_config
#     # LoRA configuration
# )


# # ============================================
# # 9. TRAIN THE MODEL
# # ============================================

# trainer.train()
# # THIS IS IT! The actual training loop
# # WHAT HAPPENS INSIDE?
# # for epoch in range(3):
# #     for batch in training_data:
# #         1. Convert text to tokens
# #         2. Forward pass (model predicts next words)
# #         3. Calculate loss (how wrong were predictions?)
# #         4. Backward pass (calculate gradients)
# #         5. Update LoRA weights
# #         6. Log metrics every 10 steps
# #         7. Save checkpoint every 200 steps
# #         8. Run validation every 200 steps


# # ============================================
# # 10. SAVE FINAL MODEL
# # ============================================

# print(f"\n💾 Saving model to {OUTPUT_DIR}...")

# trainer.model.save_pretrained(OUTPUT_DIR)
# # WHAT? Saves LoRA adapter weights (33M parameters)
# # WHERE? ./agentfoundry-finetuned/adapter_model.bin (~130MB)
# # NOTE: Base model NOT saved (it's still on HuggingFace)

# tokenizer.save_pretrained(OUTPUT_DIR)
# # WHAT? Saves tokenizer configuration
# # WHERE? ./agentfoundry-finetuned/tokenizer.json, tokenizer_config.json

# print("\n✅ Training complete!")
# print(f"📁 Model saved to: {OUTPUT_DIR}")
# print("\n🧪 Next step: Run test_model.py to validate")
# ============================================
# IMPORTS - Loading Required Libraries
# ============================================

import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)

from trl import SFTTrainer
from datasets import load_from_disk, DatasetDict


# ============================================
# 1. CONFIGURATION - Setting Up Hyperparameters
# ============================================

MODEL_NAME = "BioMistral/BioMistral-7B"
OUTPUT_DIR = "./agentfoundry-finetuned"
DATASET_PATH = "./agentfoundry_dataset"

# Shorter context for speed
MAX_SEQ_LENGTH = 512


# ============================================
# 2. LoRA CONFIGURATION - Memory-Efficient Training
# ============================================

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM"
)


# ============================================
# 3. QUANTIZATION CONFIG - Fitting 7B Model in 8GB VRAM
# ============================================

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)


# ============================================
# 4. LOAD MODEL & TOKENIZER
# ============================================

print("🔧 Loading BioMistral-7B with 4-bit quantization...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"


# ============================================
# 5. PREPARE MODEL FOR LoRA TRAINING
# ============================================

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)

print("✅ Model loaded successfully!")
print("📊 Trainable parameters:")
model.print_trainable_parameters()


# ============================================
# 6. LOAD DATASET (and SUBSAMPLE for ~12h run)
# ============================================

print("\n📚 Loading prepared dataset...")
dataset = load_from_disk(DATASET_PATH)

# Use a large but manageable subset for hackathon (~80k train, 8k val)
max_train = 50000
max_eval = 5000

train_ds = dataset["train"].shuffle(seed=42).select(
    range(min(max_train, len(dataset["train"])))
)
eval_ds = dataset["validation"].shuffle(seed=42).select(
    range(min(max_eval, len(dataset["validation"])))
)

print(f"Using {len(train_ds)} examples for training, {len(eval_ds)} for validation.")


# ============================================
# 7. TRAINING CONFIGURATION
# ============================================

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    num_train_epochs=1,                   # 1 epoch for time budget
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=200,
    save_total_limit=3,
    evaluation_strategy="steps",
    eval_steps=200,
    optim="paged_adamw_8bit",
    warmup_steps=100,
    lr_scheduler_type="cosine",
    report_to="none",
    max_grad_norm=0.3,
    weight_decay=0.001
)


# ============================================
# 8. CREATE TRAINER
# ============================================

print("\n🚀 Starting fine-tuning...")
print("⏰ Target time: ~8–12 hours on RTX 4060 (80k examples, 1 epoch)")
print("💡 TIP: Let this run while you sleep.\n")

trainer = SFTTrainer(
    model=model,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    tokenizer=tokenizer,
    args=training_args,
    peft_config=lora_config
)


# ============================================
# 9. TRAIN THE MODEL
# ============================================

trainer.train()


# ============================================
# 10. SAVE FINAL MODEL
# ============================================

print(f"\n💾 Saving model to {OUTPUT_DIR}...")

trainer.model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("\n✅ Training complete!")
print(f"📁 Model saved to: {OUTPUT_DIR}")
print("\n🧪 Next step: Run test_model.py to validate")
