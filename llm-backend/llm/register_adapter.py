import os
import json
import uuid  # New import to generate unique identifiers
from be_utils.db.flaks_db import db, Collections
from huggingface_hub import snapshot_download, hf_hub_download


class AdapterRegistry:
    """
    AdapterRegistry is responsible for registering adapter cards for a given base model
    into a MongoDB collection. Each base model document contains:
      - base_model_name: the name of the base model.
      - quantized: a boolean indicating whether the model is quantized.
      - model_type: a value indicating the model type from the adapter.
      - context_length: the maximum context_length among all adapters for the base model.
      - adapters: a list of adapter records (card data), each with its own unique adapter_uid.
      - uid: a unique identifier for the base model document.
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

    def _ensure_default_adapter(self, adapters, base_model, quantized):
        """
        Ensure that the default adapter (with project "ALL") is present in the adapters list.
        If it doesn't exist, add it with a unique adapter_uid.

        :param adapters: List of existing adapter records.
        :param base_model: The base model name to be used in the default adapter.
        :param quantized: The quantized flag to be used in the default adapter.
        :return: The updated list of adapters.
        """
        if not any(adapter.get("project") == "ALL" for adapter in adapters):
            default_adapter = {
                "name": base_model,
                "base_model": base_model,
                "quantized": quantized,
                "project": "ALL",
                "adapter_uid": str(uuid.uuid4())
            }
            adapters.append(default_adapter)
        return adapters

    def register_adapter(self, repo_id, checkpoint_step, epoch, checkpoint_repo_id=None):
        """
        Register an adapter for a base model by performing the following steps:
          1. Download the card.json file and checkpoint files.
          2. Enrich the card data with the local checkpoint path and update the adapter name (appending epoch).
          3. Generate a unique adapter_uid for the adapter (if new).
          4. Extract the base model name, quantized flag, model_type, and context_length from the card data.
          5. Insert a new base model document into Mongo or update an existing one by adding/updating the adapter.
          6. Ensure a default adapter with project "ALL" exists in the base model's adapters.
          7. Update the base model's context_length with the maximum context_length among its adapters.

        :param repo_id: Repository ID from where to download the card.json.
        :param checkpoint_step: Checkpoint step to download.
        :param epoch: Epoch number to append to the adapter name.
        :param checkpoint_repo_id: Repository ID for checkpoints. If None, defaults to repo_id.
        :return: A summary dictionary with the base model uid, adapter name, adapter_uid, quantized flag, model_type, and context_length.
        :raises ValueError: If required keys are missing in the card data.
        :raises Exception: For any other errors during registration.
        """
        try:
            if checkpoint_repo_id is None:
                checkpoint_repo_id = repo_id

            card_data = self._download_card_data(repo_id)

            # Ensure model_type is in the card data; set a default value if it's missing.
            if "model_type" not in card_data:
                card_data["model_type"] = "default"

            # Extract context_length from card_data; default to 0 if missing.
            card_data["context_length"] = card_data.get("context_length", 0)

            checkpoint_path = self._download_checkpoint(checkpoint_repo_id, checkpoint_step)
            card_data["local_adapter_path"] = checkpoint_path

            original_name = card_data.get("name", "adapter")
            adapter_name = f"{original_name}-epoch{epoch}"
            card_data["name"] = adapter_name

            # Generate a unique identifier for this adapter.
            new_adapter_uid = str(uuid.uuid4())
            card_data["adapter_uid"] = new_adapter_uid

            base_model = card_data.get("base_model")
            if not base_model:
                raise ValueError("Base model information is missing in card data.")

            quantized = card_data.get("quantized")
            if quantized is None:
                raise ValueError("Quantized flag is missing in card data.")

            # Retrieve the model_type value from card_data
            model_type = card_data["model_type"]

            existing_doc = self.collection.find_one({"base_model_name": base_model})
            if existing_doc:
                uid = existing_doc["_id"]
                adapters = existing_doc.get("adapters", [])
                found = False
                for idx, adapter in enumerate(adapters):
                    if adapter.get("name") == adapter_name:
                        # Preserve the existing adapter_uid if present.
                        if adapter.get("adapter_uid"):
                            card_data["adapter_uid"] = adapter["adapter_uid"]
                        else:
                            card_data["adapter_uid"] = new_adapter_uid
                        adapters[idx] = card_data
                        found = True
                        break
                if not found:
                    adapters.append(card_data)
                # Ensure the default adapter is present.
                adapters = self._ensure_default_adapter(adapters, base_model, quantized)
                # Compute the maximum context_length among all adapters.
                max_context_length = max(int(adapter.get("context_length", 0)) for adapter in adapters)
                self.collection.update_one(
                    {"_id": uid},
                    {"$set": {
                        "quantized": quantized,
                        "adapters": adapters,
                        "model_type": model_type,
                        "context_length": max_context_length
                    }}
                )
            else:
                # Create a new document for the base model.
                new_doc = {
                    "base_model_name": base_model,
                    "quantized": quantized,
                    "adapters": [card_data],
                    "model_type": model_type
                }
                new_doc["adapters"] = self._ensure_default_adapter(new_doc["adapters"], base_model, quantized)
                # Compute the maximum context_length among all adapters.
                max_context_length = max(int(adapter.get("context_length", 0)) for adapter in new_doc["adapters"])
                new_doc["context_length"] = max_context_length
                inserted_doc = self.collection.insert_one(new_doc)
                uid = inserted_doc.inserted_id
                self.collection.update_one({"_id": uid}, {"$set": {"uid": str(uid)}})

            return {
                "uid": str(uid),
                "base_model": base_model,
                "adapter": adapter_name,
                "adapter_uid": card_data["adapter_uid"],
                "quantized": quantized,
                "model_type": model_type,
                "context_length": max_context_length
            }
        except Exception as e:
            raise Exception(f"Failed to register adapter: {e}")

    def get_base_model(self, model_uid):
        """
        Retrieve a base model document by its uid.

        :param model_uid: The uid of the base model.
        :return: The document if found, otherwise None.
        """
        try:
            return self.collection.find_one({"uid": model_uid})
        except Exception as e:
            raise Exception(f"Error retrieving base model with uid {model_uid}: {e}")

    def list_adapters(self, model_uid):
        """
        List all adapter records for a given base model.

        :param model_uid: The base model uid.
        :return: A list of adapter records or an empty list if not found.
        """
        try:
            doc = self.get_base_model(model_uid)
            return doc.get("adapters", []) if doc else []
        except Exception as e:
            raise Exception(f"Error listing adapters for model uid {model_uid}: {e}")

    def remove_adapter(self, model_uid, adapter_uid):
        """
        Remove an adapter from a base model's document using the base model's uid and the adapter's uid.

        :param model_uid: The uid of the base model.
        :param adapter_uid: The uid of the adapter to remove.
        :return: True if an adapter was removed, False otherwise.
        """
        try:
            result = self.collection.update_one(
                {"uid": model_uid},
                {"$pull": {"adapters": {"adapter_uid": adapter_uid}}}
            )
            if result.modified_count == 0:
                raise Exception("No adapter was removed. Adapter UID may not exist.")
            return True
        except Exception as e:
            raise Exception(f"Failed to remove adapter: {e}")

    def update_adapter(self, model_uid, adapter_uid, new_data):
        """
        Update the information for a specific adapter within a base model using the base model's uid and the adapter's uid.

        :param model_uid: The uid of the base model.
        :param adapter_uid: The uid of the adapter to update.
        :param new_data: A dictionary with the new data to update the adapter record.
        :return: True if updated successfully.
        :raises ValueError: If the base model or adapter is not found.
        """
        try:
            doc = self.collection.find_one({"uid": model_uid})
            if not doc:
                raise ValueError("Base model not found.")
            adapters = doc.get("adapters", [])
            updated = False
            for idx, adapter in enumerate(adapters):
                if adapter.get("adapter_uid") == adapter_uid:
                    adapters[idx].update(new_data)
                    updated = True
                    break
            if not updated:
                raise ValueError("Adapter not found.")
            # Recompute the maximum context_length after update.
            max_context_length = max(int(adapter.get("context_length", 0)) for adapter in adapters)
            self.collection.update_one({"_id": doc["_id"]}, {"$set": {"adapters": adapters, "context_length": max_context_length}})
            return True
        except Exception as e:
            raise Exception(f"Failed to update adapter: {e}")

    def get_all_models(self):
        """
        Retrieve all base models from the collection.

        :return: A list of dictionaries containing base model names, quantized flags, adapters, model_type, and context_length.
        """
        try:
            models = list(self.collection.find({}, {"_id": 0}))
            return models
        except Exception as e:
            raise Exception(f"Error retrieving all models: {e}")

    def get_base_model_by_adapter(self, adapter_uid):
        """
        Retrieve a base model document that contains an adapter with the given adapter_uid.
        :param adapter_uid: The unique identifier for the adapter.
        :return: The base model document if found.
        :raises ValueError: If no base model contains the adapter.
        """
        doc = self.collection.find_one({"adapters.adapter_uid": adapter_uid})
        if not doc:
            raise ValueError(f"No base model found for adapter uid {adapter_uid}")
        return doc

    def get_adapter_name_by_adapter_uid(self, adapter_uid):
        """
        Retrieve the adapter name for a given adapter_uid.

        :param adapter_uid: The unique identifier for the adapter.
        :return: The adapter name if found.
        :raises ValueError: If no adapter with the given uid is found or if the adapter has no name.
        """
        try:
            doc = self.collection.find_one({"adapters.adapter_uid": adapter_uid})
            if not doc:
                raise ValueError(f"No adapter found with uid {adapter_uid}")
            for adapter in doc.get("adapters", []):
                if adapter.get("adapter_uid") == adapter_uid:
                    if "name" in adapter:
                        return adapter["name"]
                    else:
                        raise ValueError(f"Adapter with uid {adapter_uid} does not have a name.")
            raise ValueError(f"Adapter with uid {adapter_uid} not found in adapters list.")
        except Exception as e:
            raise Exception(f"Error retrieving adapter name for uid {adapter_uid}: {e}")
