from storage.data_repository import DataRepository
import json
from pathlib import Path
import os
import ijson
from utils.util import mkdir, append_to_json_list, append_to_json_object
from config.manager import config


class JsonFileHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_json(self, default_value=None):
        """Load JSON data from a file or return a default if it doesn't exist."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return json.load(file)
        return default_value if default_value is not None else {}

    def save_json(self, data, indent=None):
        """Save JSON data to a file with optional indentation."""
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=indent)

    def load_ijson(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                for item in ijson.items(file, "item"):
                    yield item  # Process items while the file is open
        else:
            return iter([])

    def append_to_list(self, obj):
        append_to_json_list(self.file_path, obj)

    def append_to_object(self, key, val):
        append_to_json_object(self.file_path, key, val)


class FileDataRepository(DataRepository):
    def __init__(self, input_file_path, output_directory):
        mkdir(output_directory)
        self.input_file = JsonFileHandler(input_file_path)

        # Derive other file names from the input file name
        base_name = Path(input_file_path).stem
        self.processed_file = JsonFileHandler(os.path.join(output_directory, f"{base_name}_processed.json"))
        self.skipped_file = JsonFileHandler(os.path.join(output_directory, f"{base_name}_skipped.json"))
        self.progress_file = JsonFileHandler(os.path.join(output_directory, f"{base_name}_progress.json"))

    def load_data(self):
        for element in self.input_file.load_ijson():
            yield element

    def save_processed_data(self, element):
        self.processed_file.append_to_list(element)

    def save_progress(self, uuid, value=""):
        self.progress_file.append_to_object(uuid, value)

    def save_skipped_data(self, data):
        self.skipped_file.append_to_list(data)

    def load_progress(self):
        return self.progress_file.load_json()

    def load_processed_data(self):
        pass

    def load_skipped_data(self):
        return self.skipped_file.load_json()

    @staticmethod
    def configure_repository():
        """Configure the repository based on config and repo_type."""
        storage_type = config.get('storage_type')

        if storage_type == 'file':
            return FileDataRepository(
                input_file_path=config.get('input.file_path'),
                output_directory=config.get('output.directory')
            )
        return None  # Default to None if not configured
