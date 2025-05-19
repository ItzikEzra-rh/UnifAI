from global_utils.config import ConfigManager
import json
import os
from pathlib import Path


def get_mongo_url():
    ip = ConfigManager().get("mongodb_ip", "0.0.0.0") or "0.0.0.0"
    port = ConfigManager().get("mongodb_port", "27017") or "27017"
    return f"mongodb://{ip}:{port}/"


def get_rabbitmq_url(user=None, password=None):
    ip = ConfigManager().get("rabbitmq_ip", "0.0.0.0") or "0.0.0.0"
    port = ConfigManager().get("rabbitmq_port", "5672") or "5672"

    if user and password:
        return f'amqp://{user}:{password}@{ip}:{port}'
    else:
        return f'amqp://{ip}:{port}'


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def sort_nested_dict(data):
    if isinstance(data, dict):
        return {key: sort_nested_dict(value) for key, value in sorted(data.items())}
    elif isinstance(data, list):
        return sorted(sort_nested_dict(x) for x in data)
    return data


def get_root_dir() -> Path:
    """
    Get the root directory of the project dynamically.

    Returns:
        Path: The root directory of the project.
    """
    # Resolve the directory containing this file
    current_file = Path(__file__).resolve()
    # Navigate up to the project root (adjust number of parents based on your structure)
    root_dir = current_file.parents[1]

    return root_dir


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
