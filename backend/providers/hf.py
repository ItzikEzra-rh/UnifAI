import json
import os
from typing import Iterator, Dict, Any
from prompt_lab.storage import HFExporter
import configparser

config = configparser.ConfigParser()
config.read("config/backend.cfg")

def json_record_provider(json_path: str) -> Iterator[Dict[str, Any]]:
    """
    Generator function to yield records from a JSON file.
    
    Args:
        json_path (str): Path to the JSON file.
    
    Yields:
        Dict[str, Any]: Each record from the JSON file.
    """
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        if isinstance(data, list):  # Ensure JSON structure is a list of dictionaries
            for record in data:
                yield record
        else:
            raise ValueError("JSON file must contain a list of dictionaries.")


def upload_json_to_hf(json_path: str, project_name: str):
    """
    Reads a JSON file and uploads it to Hugging Face Hub using HFExporter.
    
    Args:
        json_path (str): Path to the JSON file.
    
    Returns:
        str: URL of the uploaded dataset.
    """
    user_name = config.get("hf", "HF_USER_NAME", fallback=None)
    data_set = config.get("hf", "HF_DATA_SET", fallback=None)
    token = config.get("hf", "HF_TOKEN", fallback=None)
    batch_size = config.getint("hf", "HF_BATCH_SIZE", fallback=1000)
    export_format = config.get("hf", "HF_EXPORT_FORMAT", fallback="json").lower()

    repo_id = f"{user_name}/{data_set}"
    if not repo_id or not token:
        raise ValueError("Missing required Hugging Face credentials. Set HF_REPO_ID and HF_TOKEN.")

    record_generator = json_record_provider(json_path)
    exporter = HFExporter(repo_id=repo_id, file_name=project_name, token=token, batch_size=batch_size, export_format=export_format)
    upload_url = exporter.export(record_generator)
    
    print(f"✅ File successfully uploaded! Access it here: {upload_url}")
    return upload_url
