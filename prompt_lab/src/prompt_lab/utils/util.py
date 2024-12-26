from config.manager import config
import json
import ijson
import os


def get_mongo_url():
    path = config.get("mongodb.url")
    port = config.get("mongodb.port")
    return path.format(port=port)


def get_rabbitmq_url():
    path = config.get("rabbitmq.url")
    port = config.get("rabbitmq.port")
    return path.format(port=port)


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def append_to_json_list(file_path, new_item):
    """
    Append a single item to an on-disk JSON array with minimal overhead.
    Creates [ new_item ] if file does not exist.
    Otherwise, manipulates the last byte(s) to insert a comma and the new item.
    """
    if not os.path.exists(file_path):
        # Create a new array file
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump([new_item], file, ensure_ascii=False)
    else:
        with open(file_path, 'r+b') as file:
            file.seek(-1, 2)  # Go to the last character in the file
            last_char = file.read(1)
            if last_char != b']':
                # If it's not a ']', assume it's empty or invalid
                # Insert [new_item]
                file.seek(0, 2)  # go to end again
                file.write(b'[')
                file.write(json.dumps(new_item, ensure_ascii=False).encode('utf-8'))
                file.write(b']')
            else:
                # We have a valid JSON array; remove the final bracket, add ',', item, then ']'
                file.seek(-1, 2)
                file.truncate()
                file.write(b',')
                file.write(json.dumps(new_item, ensure_ascii=False).encode('utf-8'))
                file.write(b']')


def append_multiple_to_json_list(file_path, items):
    """
    Append multiple items (list of dicts) to an on-disk JSON array with minimal overhead.
    Each call manipulates the last character of the file to insert a comma-separated list.
    """
    if not items:
        return  # Nothing to do
    if not os.path.exists(file_path):
        # Create a new array file with all items
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(items, file, ensure_ascii=False)
    else:
        with open(file_path, 'r+b') as file:
            file.seek(-1, 2)
            last_char = file.read(1)
            if last_char != b']':
                # File is empty or invalid, start fresh
                file.seek(0, 2)
                file.write(b'[')
                file.write(_items_to_comma_delimited_json(items))
                file.write(b']')
            else:
                # Valid array, remove the final bracket and add items
                file.seek(-1, 2)
                file.truncate()
                file.write(b',')
                file.write(_items_to_comma_delimited_json(items))
                file.write(b']')


def _items_to_comma_delimited_json(items):
    """
    Helper to convert a list of Python objects into a comma-delimited
    JSON string without brackets, e.g. item1,item2
    """
    return b','.join(json.dumps(item, ensure_ascii=False).encode('utf-8') for item in items)


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
