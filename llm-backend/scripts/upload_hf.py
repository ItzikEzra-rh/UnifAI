max_seq_length = 8192  # Choose any! Llama 3 is up to 8k
dtype = None
load_in_4bit = True  # Use 4bit quantization to reduce memory usage. Can be False.

from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/home/instruct/openshift-qe-infra/openshift-qe-infra-training-loraRank16-loraAlpha16/checkpoint-12730"
)
# FastLanguageModel.for_inference(model)  # Enable native 2x faster inferenc

model.push_to_hub("oodeh/openshift-qe-r16-a16", token = "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") # Online saving
tokenizer.push_to_hub("oodeh/openshift-qe-r16-a16", token = "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") # Online saving
