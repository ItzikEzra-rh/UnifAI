import os
import json
from be_utils.db.flaks_db import db, Collections
from huggingface_hub import snapshot_download, hf_hub_download


class AdapterRegistry:
    """
    AdapterRegistry is responsible for registering adapter cards for a given base model
    into a MongoDB collection. Each base model document contains:
      - base_model_name: the name of the base model.
      - quantized: a boolean indicating whether the model is quantized.
      - adapters: a list of adapter records (card data).
    """

    def __init__(self, collection_name='RegisteredModels', auth_token=None):
        """
        Initialize the registry with the given MongoDB collection name and an optional auth token.
        """
        self.db = db()
        self.collection = Collections.by_name(collection_name)
        self.auth_token = auth_token

    def _download_card_data(self, repo_id):
        """
        Download and load the card.json file from a given repository.

        :param repo_id: The repository ID to download from.
        :return: A dictionary with the card data.
        :raises RuntimeError: If the download or file reading fails.
        """
        try:
            # Download card.json from Hugging Face Hub
            card_path = hf_hub_download(
                repo_id=repo_id,
                filename="card.json",
                use_auth_token=self.auth_token
            )
            print(card_path)
            with open(card_path, 'r') as file:
                card_data = json.load(file)
            return card_data
        except Exception as e:
            raise RuntimeError(f"Error downloading or reading card.json: {e}")

    def _download_checkpoint(self, checkpoint_repo_id, checkpoint_step):
        """
        Download the checkpoint files for the adapter using snapshot_download.

        :param checkpoint_repo_id: Repository ID for the checkpoint files.
        :param checkpoint_step: The checkpoint step number (used to filter files).
        :return: The local path to the downloaded checkpoint directory.
        :raises RuntimeError: If the checkpoint download fails.
        """
        try:
            downloaded_path = snapshot_download(
                repo_id=checkpoint_repo_id,
                allow_patterns=[f"checkpoint-{checkpoint_step}/*"],
                use_auth_token=self.auth_token
            )
            checkpoint_path = os.path.join(downloaded_path, f"checkpoint-{checkpoint_step}")
            if not os.path.exists(checkpoint_path):
                raise FileNotFoundError(f"Checkpoint path not found: {checkpoint_path}")
            return checkpoint_path
        except Exception as e:
            raise RuntimeError(f"Error downloading checkpoint: {e}")

    def register_adapter(self, repo_id, checkpoint_step, epoch, checkpoint_repo_id=None):
        """
        Register an adapter for a base model by performing the following steps:
          1. Download the card.json file and checkpoint files.
          2. Enrich the card data with the local checkpoint path and update the adapter name (appending epoch).
          3. Extract the base model name and quantized flag from the card data.
          4. Insert a new base model document into Mongo or update an existing one by adding/updating the adapter.

        :param repo_id: Repository ID from where to download the card.json.
        :param checkpoint_step: Checkpoint step to download.
        :param epoch: Epoch number to append to the adapter name.
        :param checkpoint_repo_id: Repository ID for checkpoints. If None, defaults to repo_id.
        :return: A summary dictionary with the base model name, adapter name, and quantized flag.
        :raises ValueError: If required keys are missing in the card data.
        """
        # Use repo_id for checkpoints if not provided separately
        if checkpoint_repo_id is None:
            checkpoint_repo_id = repo_id

        card_data = self._download_card_data(repo_id)
        checkpoint_path = self._download_checkpoint(checkpoint_repo_id, checkpoint_step)
        card_data["local_adapter_path"] = checkpoint_path

        original_name = card_data.get("name", "adapter")
        adapter_name = f"{original_name}-epoch{epoch}"
        card_data["name"] = adapter_name

        base_model = card_data.get("base_model")
        if not base_model:
            raise ValueError("Base model information is missing in card data.")

        quantized = card_data.get("quantized")
        if quantized is None:
            raise ValueError("Quantized flag is missing in card data.")

        existing_doc = self.collection.find_one({"base_model_name": base_model})
        if existing_doc:
            uid = existing_doc["_id"]  # Use existing model's MongoDB ID
            adapters = existing_doc.get("adapters", [])
            found = False
            for idx, adapter in enumerate(adapters):
                if adapter.get("name") == adapter_name:
                    adapters[idx] = card_data
                    found = True
                    break
            if not found:
                adapters.append(card_data)

            self.collection.update_one(
                {"_id": uid},
                {"$set": {"quantized": quantized, "adapters": adapters}}
            )
        else:
            new_doc = {
                "base_model_name": base_model,
                "quantized": quantized,
                "adapters": [card_data]
            }
            inserted_doc = self.collection.insert_one(new_doc)
            uid = inserted_doc.inserted_id  # Assign MongoDB ID as UID
            self.collection.update_one({"_id": uid}, {"$set": {"uid": str(uid)}})

        return {"uid": str(uid), "base_model": base_model, "adapter": adapter_name, "quantized": quantized}

    def get_base_model(self, model_uid):
        """
        Retrieve a base model document by its name.

        :param model_uid: The uid of the base model.
        :return: The document if found, otherwise None.
        """
        return self.collection.find_one({"uid": model_uid})

    def list_adapters(self, model_uid):
        """
        List all adapter records for a given base model.

        :param model_uid: The base model uid.
        :return: A list of adapter records or an empty list if not found.
        """
        doc = self.get_base_model(model_uid)
        return doc.get("adapters", []) if doc else []

    def remove_adapter(self, base_model_name, adapter_name):
        """
        Remove an adapter from a base model's document.

        :param base_model_name: The name of the base model.
        :param adapter_name: The name of the adapter to remove.
        :return: True if an adapter was removed, False otherwise.
        """
        result = self.collection.update_one(
            {"base_model_name": base_model_name},
            {"$pull": {"adapters": {"name": adapter_name}}}
        )
        return result.modified_count > 0

    def update_adapter(self, base_model_name, adapter_name, new_data):
        """
        Update the information for a specific adapter within a base model.

        :param base_model_name: The name of the base model.
        :param adapter_name: The adapter to update.
        :param new_data: A dictionary with the new data to update the adapter record.
        :return: True if updated successfully.
        :raises ValueError: If the base model or adapter is not found.
        """
        doc = self.get_base_model(base_model_name)
        if not doc:
            raise ValueError("Base model not found.")
        adapters = doc.get("adapters", [])
        updated = False
        for idx, adapter in enumerate(adapters):
            if adapter.get("name") == adapter_name:
                adapters[idx].update(new_data)
                updated = True
                break
        if not updated:
            raise ValueError("Adapter not found.")
        self.collection.update_one({"_id": doc["_id"]}, {"$set": {"adapters": adapters}})
        return True

    def get_all_models(self):
        """
        Retrieve all base models from the collection.

        :return: A list of dictionaries containing base model names, quantized flags, and adapters.
        """
        models = list(self.collection.find({}, {"_id": 0}))  # Exclude MongoDB `_id` field
        return models
