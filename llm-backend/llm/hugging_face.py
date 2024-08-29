from datetime import datetime
from be_utils.db.flaks_db import *
from huggingface_hub import HfApi


class HuggingFaceAPI:
    def __init__(self):
        # Initialize the Hugging Face API client
        self.api = HfApi()

    def list_repo_files(self, repo_id, repo_type="model"):
        """
        List all files in a specified Hugging Face repository.

        :param repo_id: The repository ID (e.g., 'username/repo_name').
        :return: A list of file paths in the repository.
        """
        try:
            files = self.api.list_repo_files(repo_id=repo_id, repo_type=repo_type)
            files = [file for file in files if not file.startswith('.')]
            return files
        except Exception as e:
            print(f"An error occurred while fetching files: {e}")
            return []


class HFTokenManager:
    # Class variable to hold the token
    _token = None

    def __init__(self, collection_name='huggingFaceTokens'):
        self.collection = Collections.by_name(collection_name)

    def save_token(self, token):
        # Save the token in MongoDB with a timestamp
        token_data = {
            "token": token,
            "created_at": datetime.utcnow()
        }
        self.collection.insert_one(token_data)
        HFTokenManager._token = token

    def retrieve_token(self):
        # Retrieve the latest token from MongoDB
        latest_token_entry = self.collection.find_one(
            sort=[("created_at", -1)]
        )
        if latest_token_entry:
            HFTokenManager._token = latest_token_entry['token']
        return HFTokenManager._token
