from config.manager import config
from storage.file_data_repository import FileDataRepository
import json
import os


def get_mongo_url():
    path = config.get("mongodb.url")
    port = config.get("mongodb.port")
    return path.format(port=port)


def get_rabbitmq_url():
    path = config.get("rabbitmq.url")
    port = config.get("rabbitmq.port")
    return path.format(port=port)


def configure_repository():
    """Configure the repository based on config and repo_type."""
    storage_type = config.get('storage_type')

    if storage_type == 'file':
        return FileDataRepository(
            input_file_path=config.get('input.file_path'),
            output_directory=config.get('output.directory')
        )
    return None  # Default to None if not configured


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
