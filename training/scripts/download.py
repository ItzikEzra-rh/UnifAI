import os
from huggingface_hub import HfApi, snapshot_download

# Define repository details
REPO_ID = "oodeh/oadp-tag-training-qwen14b-q4bit-checkpoints"  # Replace with your repo
LOCAL_DIR = "/tmp/huggingface_download"  # Replace with your desired download location

# Ensure the directory exists
os.makedirs(LOCAL_DIR, exist_ok=True)

# Initialize API (token is automatically read from ENV)
api = HfApi()

# Download the entire repo or a specific folder
snapshot_download(
    repo_id=REPO_ID,
    repo_type="model",
    local_dir=LOCAL_DIR,
    local_dir_use_symlinks=False  # Set to True for efficient disk usage
)

print(f"✅ Download complete. Files saved in: {LOCAL_DIR}")
