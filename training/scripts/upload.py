import os
from huggingface_hub import HfApi, create_repo, upload_large_folder

# Define repository details
REPO_ID = "oodeh/oadp-tag-training-qwen14b-q4bit-checkpoints"
LOCAL_DIR = "/tmp/LLaMA-Factory/saves/Qwen2.5-Coder-14B-Instruct/lora/train_2025-02-17-02-33-51"

# Initialize API (token will be automatically read from ENV)
api = HfApi()

# Create the repository (if it doesn't exist)
create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True)

# Upload the large folder efficiently
upload_large_folder(
    folder_path=LOCAL_DIR,
    repo_id=REPO_ID,
    repo_type="model"
)

print(f"✅ Successfully uploaded {LOCAL_DIR} to {REPO_ID}.")
