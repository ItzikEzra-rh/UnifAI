import os
import json
from abc import ABC, abstractmethod


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


class DataRepository(ABC):
    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def load_processed_data(self):
        pass

    @abstractmethod
    def load_skipped_data(self):
        pass

    @abstractmethod
    def save_processed_data(self, data):
        pass

    @abstractmethod
    def save_progress(self, data):
        pass

    @abstractmethod
    def load_progress(self):
        pass

    @abstractmethod
    def save_skipped_data(self, data):
        pass
