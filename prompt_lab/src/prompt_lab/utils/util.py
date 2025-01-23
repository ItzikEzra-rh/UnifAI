from prompt_lab.config import ConfigManager
import json
import os
from pathlib import Path


def get_mongo_url():
    ip = ConfigManager().get("mongodb_ip", "0.0.0.0") or "0.0.0.0"
    port = ConfigManager().get("mongodb_port", "27017") or "27017"
    return f"mongodb://{ip}:{port}/"


def get_rabbitmq_url():
    ip = ConfigManager().get("rabbitmq_ip", "0.0.0.0") or "0.0.0.0"
    port = ConfigManager().get("rabbitmq_port", "5672") or "5672"
    return f"amqp://{ip}:{port}/"


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def append_to_json_list(file_path, new_item):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump([new_item], file)
    else:
        with open(file_path, 'r+b') as file:
            file.seek(-1, 2)  # Go to the last character
            if file.read(1) != b']':
                file.write(b'[')
                file.write(json.dumps(new_item).encode())
                file.write(b']')
            else:
                file.seek(-1, 2)
                file.truncate()
                file.write(b',')
                file.write(json.dumps(new_item).encode())
                file.write(b']')


def append_to_json_object(file_path, new_key, new_value):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({new_key: new_value}, file)
    else:
        with open(file_path, 'r+b') as file:
            file.seek(-1, 2)  # Go to the last character
            last_char = file.read(1)
            if last_char != b'}':
                # File doesn't end with '}', assume it's empty or invalid
                file.seek(0)
                file.truncate()
                json.dump({new_key: new_value}, file)
            else:
                file.seek(-1, 2)
                file.truncate()
                file.write(b',')
                file.write(json.dumps({new_key: new_value})[1:-1].encode())
                file.write(b'}')


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
