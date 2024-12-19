# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer
# device = "cuda" # or "cpu"
# model_path = "ibm-granite/granite-3b-code-instruct-128k"
# tokenizer = AutoTokenizer.from_pretrained(model_path)
# # drop device_map if running on CPU
# model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device)
# model.eval()
#
# ###########################
#
# inputs = tokenizer(
#     [
#         """<user>Write a Robot Framework Test that Create a test:
# create a pod.
#  <assistant>"""
#     ], return_tensors = "pt").to("cuda")
#
# from transformers import TextStreamer
# text_streamer = TextStreamer(tokenizer)
# _ = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128000)


import os  # Operating system functionalities
import torch  # PyTorch library for deep learning
from datasets import load_dataset  # Loading datasets for training
from transformers import (
    AutoModelForCausalLM,  # AutoModel for language modeling tasks
    AutoTokenizer,  # AutoTokenizer for tokenization
    BitsAndBytesConfig,  # Configuration for BitsAndBytes
    HfArgumentParser,  # Argument parser for Hugging Face models
    TrainingArguments,  # Training arguments for model training
    pipeline,  # Creating pipelines for model inference
    logging,  # Logging information during training
)
from peft import LoraConfig, PeftModel  # Packages for parameter-efficient fine-tuning (PEFT)
from trl import SFTTrainer


def find_latest_checkpoint(output_dir):
    # List all checkpoint directories
    checkpoints = [d for d in os.listdir(output_dir) if d.startswith('checkpoint-')]

    # If there are no checkpoints, return None
    if not checkpoints:
        return ""

    # Sort checkpoints by their number (assumes the format 'checkpoint-<number>')
    checkpoints = sorted(checkpoints, key=lambda x: int(x.split('-')[1]), reverse=True)

    # Return the path to the latest checkpoint
    return os.path.join(output_dir, checkpoints[0])


output_dir = "/home/instruct/results"

# Find the latest checkpoint
latest_checkpoint = find_latest_checkpoint(output_dir) if os.path.exists(output_dir) else ""
if latest_checkpoint:
    print(f"latest checkpoint {latest_checkpoint} - continue training from this checkpoint")
else:
    print("no checkpoint - new run")

model_name = "ibm-granite/granite-8b-code-instruct-128k"

################################################################################
# bitsandbytes parameters
################################################################################

# Activate 4-bit precision base model loading
use_4bit = True

# Compute dtype for 4-bit base models
bnb_4bit_compute_dtype = "float16"

# Quantization type (fp4 or nf4)
bnb_4bit_quant_type = "nf4"

# Activate nested quantization for 4-bit base models (double quantization)
use_nested_quant = False

output_dir = "results"

# Number of training epochs
num_train_epochs = 6

# Enable fp16/bf16 training (set bf16 to True with an A100)
fp16 = True  # If using mixed precision, ensure this is correctly set
bf16 = False

per_device_train_batch_size = 1

gradient_accumulation_steps = 4

# Enable gradient checkpointing
gradient_checkpointing = True

# Maximum gradient normal (gradient clipping)
max_grad_norm = 0.3

# Initial learning rate (AdamW optimizer)
learning_rate = 2e-4

# Weight decay to apply to all layers except bias/LayerNorm weights
weight_decay = 0.001

# Optimizer to use
optim = "paged_adamw_32bit"

# Learning rate schedule (constant a bit better than cosine)
lr_scheduler_type = "constant"

# Number of training steps (overrides num_train_epochs)
max_steps = -1

# Ratio of steps for a linear warmup (from 0 to learning rate)
warmup_ratio = 0.03

# Group sequences into batches with same length
# Saves memory and speeds up training considerably
group_by_length = True

# Save checkpoint every X updates steps
save_steps = 25
save_total_limit = 4
# Log every X updates steps
logging_steps = 1

# Maximum sequence length to use
max_seq_length = 4096

# Pack multiple short examples in the same input sequence to increase efficiency
packing = False

# Load the entire model on the GPU 0
device_map = {"": 0}

new_model = f"{model_name}-finetuned-{max_seq_length}-maxSeqLen-{per_device_train_batch_size * gradient_accumulation_steps}-batchsize-{num_train_epochs}-epocs"

compute_dtype = getattr(torch, bnb_4bit_compute_dtype)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=use_4bit,
    bnb_4bit_quant_type=bnb_4bit_quant_type,
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=use_nested_quant,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map=device_map
)

model.config.use_cache = False
model.config.pretraining_tp = 1

tokenizer = AutoTokenizer.from_pretrained(model_name)
EOS_TOKEN = tokenizer.eos_token


def formatting_function(examples):
    code_list = examples["code"]
    prompt_list = examples["prompt"]

    texts = []
    for prompt, code in zip(prompt_list, code_list):
        text = f"""<user>{prompt}<assistant>{code}""" + EOS_TOKEN
        texts.append(text)
    return {"text": texts, }


dataset = load_dataset("oodeh/NcsRobotTestFramework",
                       data_files='ncs_full_tests_822.json',
                       split="train")

dataset = dataset.map(formatting_function, batched=True, )

lora_r = 16
# Alpha parameter for LoRA scaling
lora_alpha = 16
# Dropout probability for LoRA layers
lora_dropout = 0.1
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj", ]

peft_config = LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=target_modules
)

training_arguments = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=num_train_epochs,
    per_device_train_batch_size=per_device_train_batch_size,
    gradient_accumulation_steps=gradient_accumulation_steps,
    gradient_checkpointing=gradient_checkpointing,
    optim=optim,
    save_steps=save_steps,
    save_total_limit=save_total_limit,
    logging_steps=logging_steps,
    learning_rate=learning_rate,
    weight_decay=weight_decay,
    fp16=fp16,
    bf16=bf16,
    max_grad_norm=max_grad_norm,
    max_steps=max_steps,
    warmup_ratio=warmup_ratio,
    group_by_length=group_by_length,
    lr_scheduler_type=lr_scheduler_type,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=packing,
)

if latest_checkpoint:
    print(latest_checkpoint)
    trainer.train(resume_from_checkpoint=latest_checkpoint)
else:
    trainer.train()

trainer.model.save_pretrained(new_model)
tokenizer.save_pretrained(new_model)
