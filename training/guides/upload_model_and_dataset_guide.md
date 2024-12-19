# Uploading a Model and Dataset to Hugging Face

This guide will walk you through the process of uploading a **model** and a **dataset** to the Hugging Face Hub. Don't worry—it's simple! We'll explain every step like you're learning for the first time.

---

## Prerequisites

Before you start, make sure you have:

1. **A Hugging Face Account**:
   - Create an account at [Hugging Face](https://huggingface.co) if you don't already have one.

2. **Install the Hugging Face Hub Library**:
   - Run this command in your terminal to install the library:
     ```bash
     pip install huggingface_hub
     ```

3. **Authenticate with Hugging Face**:
   - Run the following command and log in with your Hugging Face account credentials:
     ```bash
     huggingface-cli login
     ```

---

## Uploading a Model

### What You Need
- A folder containing your model files (e.g., `config.json`, `pytorch_model.bin`, etc.).
- A unique name for your model repository.

### Steps to Upload a Model

1. **Prepare Your Variables**:
   ```python
   from huggingface_hub import HfApi, upload_folder

   # Define variables
   model_dir = "path-to-your-model/"  # Path to your local model directory
   repo_name = "your-model-repo-name"  # Name of the model repository
   username = "your-username"  # Your Hugging Face username
   repo_id = f"{username}/{repo_name}"  # Full repo name (e.g., "username/your-model-name")
   ```

2. **Create the Repository**:
   - This step creates a place on Hugging Face Hub to store your model.
   ```python
   # Initialize Hugging Face API
   api = HfApi()

   # Create the repository if it doesn’t already exist
   api.create_repo(repo_id, exist_ok=True)
   ```

3. **Upload the Model**:
   - Upload all files in your model folder to the repository.
   ```python
   # Upload the entire directory to the repository
   upload_folder(
       folder_path=model_dir,
       repo_id=repo_id,
       commit_message="Initial upload of the model"
   )

   print(f"Model uploaded successfully to https://huggingface.co/{repo_id}")
   ```

---

## Uploading a Dataset

### What You Need
- A folder containing your dataset (e.g., JSON, CSV files).
- A unique name for your dataset repository.

### Steps to Upload a Dataset

1. **Prepare Your Variables**:
   ```python
   from huggingface_hub import HfApi, upload_folder

   # Define variables
   dataset_dir = "path-to-your-dataset/"  # Path to your local dataset directory
   repo_name = "your-dataset-repo-name"  # Name of the dataset repository
   username = "your-username"  # Your Hugging Face username
   repo_id = f"{username}/{repo_name}"  # Full repo name (e.g., "username/your-dataset-name")
   ```

2. **Create the Repository**:
   - This step creates a place on Hugging Face Hub to store your dataset.
   ```python
   # Initialize Hugging Face API
   api = HfApi()

   # Create the repository if it doesn’t already exist
   api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
   ```

3. **Upload the Dataset**:
   - Upload all files in your dataset folder to the repository.
   ```python
   # Upload the entire directory to the repository
   upload_folder(
       folder_path=dataset_dir,
       repo_id=repo_id,
       repo_type="dataset",
       commit_message="Initial upload of the dataset"
   )

   print(f"Dataset uploaded successfully to https://huggingface.co/datasets/{repo_id}")
   ```

---

## Full Example Code

### Uploading a Model
Here’s the complete code to upload a model:
```python
from huggingface_hub import HfApi, upload_folder

# Define variables
model_dir = "path-to-your-model/"  # Path to your local model directory
repo_name = "your-model-repo-name"  # Name of the model repository
username = "your-username"  # Your Hugging Face username
repo_id = f"{username}/{repo_name}"  # Full repo name

# Initialize Hugging Face API
api = HfApi()

# Create the repository if it doesn’t already exist
api.create_repo(repo_id, exist_ok=True)

# Upload the entire directory to the repository
upload_folder(
    folder_path=model_dir,
    repo_id=repo_id,
    commit_message="Initial upload of the model"
)

print(f"Model uploaded successfully to https://huggingface.co/{repo_id}")
```

### Uploading a Dataset
Here’s the complete code to upload a dataset:
```python
from huggingface_hub import HfApi, upload_folder

# Define variables
dataset_dir = "path-to-your-dataset/"  # Path to your local dataset directory
repo_name = "your-dataset-repo-name"  # Name of the dataset repository
username = "your-username"  # Your Hugging Face username
repo_id = f"{username}/{repo_name}"  # Full repo name

# Initialize Hugging Face API
api = HfApi()

# Create the repository if it doesn’t already exist
api.create_repo(repo_id, repo_type="dataset", exist_ok=True)

# Upload the entire directory to the repository
upload_folder(
    folder_path=dataset_dir,
    repo_id=repo_id,
    repo_type="dataset",
    commit_message="Initial upload of the dataset"
)

print(f"Dataset uploaded successfully to https://huggingface.co/datasets/{repo_id}")
```

---

## What Happens Behind the Scenes

- **`HfApi.create_repo`**:
  - This creates a new repository on Hugging Face Hub.
  - If it already exists, it won’t create a duplicate.

- **`upload_folder`**:
  - This uploads all the files from the specified folder to the Hugging Face Hub.
  - It adds a commit message (like a note) to explain what was uploaded.

- **Repository Types**:
  - Use `repo_type="dataset"` for datasets and leave it as default for models.

---

## Where to See Your Uploads

- **Models**: Visit [https://huggingface.co/{username}/{repo_name}](https://huggingface.co/{username}/{repo_name})
- **Datasets**: Visit [https://huggingface.co/datasets/{username}/{repo_name}](https://huggingface.co/datasets/{username}/{repo_name})

---

Congratulations! 🎉 You’ve successfully uploaded a model and a dataset to Hugging Face Hub!

