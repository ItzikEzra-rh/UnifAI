from storage.data_repository import DataRepository
import json
from pathlib import Path
import os
import ijson


class FileHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_json(self, default_value=None):
        """Load JSON data from a file or return a default if it doesn't exist."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return json.load(file)
        return default_value if default_value is not None else []

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


class FileDataRepository(DataRepository):
    def __init__(self, input_file_path, output_directory):
        self.input_file = FileHandler(input_file_path)

        # Derive other file names from the input file name
        base_name = Path(input_file_path).stem
        self.processed_file = FileHandler(os.path.join(output_directory, f"{base_name}_processed.json"))
        self.skipped_file = FileHandler(os.path.join(output_directory, f"{base_name}_skipped.json"))
        self.progress_file = FileHandler(os.path.join(output_directory, f"{base_name}_progress.json"))

    def load_data(self):
        for element in self.input_file.load_ijson():
            yield element

    def save_processed_data(self, data):
        self.processed_file.save_json(data, indent=4)

    def save_progress(self, current_index):
        self.progress_file.save_json({"prompt_index": current_index})

    def save_skipped_data(self, data):
        self.skipped_file.save_json(data, indent=4)

    def load_progress(self):
        progress_data = self.progress_file.load_json(default_value={"prompt_index": 0})
        return progress_data.get('prompt_index', 0)

    def load_processed_data(self):
        return self.processed_file.load_json()

    def load_skipped_data(self):
        return self.skipped_file.load_json()
