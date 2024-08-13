max_seq_length = 8192  # Choose any! Llama 3 is up to 8k
dtype = None
load_in_4bit = True  # Use 4bit quantization to reduce memory usage. Can be False.

from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "lora_model_150k", # YOUR MODEL YOU USED FOR TRAINING
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
FastLanguageModel.for_inference(model) # Enable native 2x faster inferenc


model.push_to_hub_merged("oodeh/llama-3-8b-Instruct-bnb-4bit-ncs-robot-tests-data150k-finetuned-412test2prompts-12epochs", tokenizer, save_method = "merged_4bit_forced", token="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")
