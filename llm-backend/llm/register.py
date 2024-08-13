from be_utils.db.flaks_db import *
from huggingface_hub import hf_hub_download
import json
import os


class RegisterModel:
    def __init__(self, collection_name='RegisteredModels', auth_token=None):
        self.db = db()
        self.collection = Collections.by_name(collection_name)
        self.auth_token = auth_token

    def register_model(self, model_url):
        # Extract the repo_id from the URL
        repo_id = self._extract_repo_id(model_url)

        # Attempt to download and process the card.json or fallback to config.json
        model_data = self._fetch_and_parse_model_data(repo_id)

        if self.model_exists(model_data):
            return f"Model '{model_data['base_model']}' for project '{model_data['project']}' already exists."

        # Insert the model data into the database
        result = self.collection.insert_one(model_data)
        model_id = str(result.inserted_id)
        return model_id

    def update_model(self, model_id, **kwargs):
        model_id = as_object_id(model_id)
        update_data = {"$set": kwargs}
        result = self.collection.update_one({"_id": model_id}, update_data)
        return result.modified_count

    def get_model(self, model_id):
        model_id = as_object_id(model_id)
        model = self.collection.find_one({"_id": model_id})
        if model:
            model['_id'] = str(model['_id'])
        return model

    def get_models_by_project(self, project):
        models = self.collection.find({"project": project})
        return [{**model, '_id': str(model['_id'])} for model in models]

    def get_models(self):
        models = self.collection.find({})
        return [{**model, '_id': str(model['_id'])} for model in models]

    def model_exists(self, model_data):
        return self.collection.find_one({
            "base_model": model_data['base_model'],
            "project": model_data['project'],
            "context_length": model_data['context_length'],
            "model_type": model_data['model_type'],
            "checkpoint": model_data.get('checkpoint', ""),
            "huggingface_url": model_data.get('huggingface_url', ""),
            "hf_repo_id": model_data.get('hf_repo_id', ""),
        }) is not None

    def _fetch_and_parse_model_data(self, repo_id):
        # Attempt to download card.json, fallback to config.json
        card_path = None
        try:
            card_path = hf_hub_download(repo_id=repo_id, filename="card.json", use_auth_token=self.auth_token)
            with open(card_path, 'r') as f:
                card_data = json.load(f)

            model_data = {
                "name": f"{card_data.get('model_type', 'Unknown')} {card_data.get('project', 'Unknown')} {repo_id}",
                "base_model": card_data.get('base_model', 'Unknown'),
                "project": card_data.get('project', 'Unknown'),
                "context_length": card_data.get('context_length', 0),
                "model_type": card_data.get('model_type', 'Unknown'),
                "finetune_steps": card_data.get('finetune_steps', []),
                "checkpoint": card_data.get('checkpoint', ""),
                "huggingface_url": f"https://huggingface.co/{repo_id}",
                "hf_repo_id": repo_id
            }

            if model_data['model_type'] not in ['finetuned', 'checkpoint']:
                raise ValueError("Invalid model type. Must be 'finetuned' or 'checkpoint'.")

        except Exception:
            if card_path and os.path.exists(card_path):
                os.remove(card_path)
            config_path = hf_hub_download(repo_id=repo_id, filename="config.json", use_auth_token=self.auth_token)
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            model_data = {
                "name": f"{config_data.get('model_type', 'Unknown')} {repo_id}",
                "base_model": config_data.get('_name_or_path', 'Unknown'),
                "project": 'Unknown',
                "context_length": config_data.get('max_position_embeddings', 0),
                "model_type": 'foundational',
                "checkpoint": "",
                "huggingface_url": f"https://huggingface.co/{repo_id}",
                "hf_repo_id": repo_id
            }

            if os.path.exists(config_path):
                os.remove(config_path)

        finally:
            if card_path and os.path.exists(card_path):
                os.remove(card_path)

        return model_data

    def _extract_repo_id(self, model_url):
        # Assuming model_url is in the format "https://huggingface.co/{repo_id}"
        return '/'.join(model_url.rstrip('/').split('/')[-2:])

# This class is now cleaner, more efficient, and handles both scenarios (card.json and config.json) gracefully.
