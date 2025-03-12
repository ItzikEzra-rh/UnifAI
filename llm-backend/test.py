import os
import time
import asyncio
from transformers import AutoTokenizer
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from vllm.lora.request import LoRARequest
from huggingface_hub import snapshot_download

# Define base directory
base_dir = os.path.expanduser("~/home/instruct/test")  # Expands ~ to full home path

# Ensure base directory exists
os.makedirs(base_dir, exist_ok=True)

# Download the specific checkpoint
downloaded_path = snapshot_download(
    repo_id="oodeh/ncs-tag-training-qwen14b-q4bit-checkpoints",
    allow_patterns=["checkpoint-360/*"],  # Ensures all files inside are downloaded
    local_dir=base_dir,
    local_dir_use_symlinks=False  # Ensures files are copied, not symlinked
)

# Full path where the checkpoint is stored
checkpoint_path = os.path.join(base_dir, "checkpoint-360")

print(f"Checkpoint downloaded to: {checkpoint_path}")

# Load tokenizer
tokenizer_path = "Qwen/Qwen2.5-Coder-14B-Instruct"  # Adjust if needed
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# Define chat messages
messages = [
    {"role": "system", "content": "this context is about NCS project"},
    {"role": "user", "content": """Write a test in Robot that shutdown ncs cluster then start it up and verify its up."""}
]

# Format the chat messages using the tokenizer
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

# Initialize the asynchronous language model engine
engine_args = AsyncEngineArgs(
    model=tokenizer_path,
    enable_lora=True,
    quantization="bitsandbytes",
    load_format="bitsandbytes"
)
llm = AsyncLLMEngine.from_engine_args(engine_args)

# Define sampling parameters
sampling_params = SamplingParams(
    temperature=0.0,
    max_tokens=16000,
    top_p=0.9
)

async def generate_streaming(formatted_prompt):
    request_id = str(time.monotonic())
    lora_request = LoRARequest("sql_adapter", 1, checkpoint_path)
    results_generator = llm.generate(
        formatted_prompt,
        sampling_params,
        request_id=request_id,
        lora_request=lora_request
    )
    previous_text = ""
    async for request_output in results_generator:
        text = request_output.outputs[0].text
        print(text[len(previous_text):], end="", flush=True)
        previous_text = text

# Run the asynchronous function
asyncio.run(generate_streaming(formatted_prompt))
