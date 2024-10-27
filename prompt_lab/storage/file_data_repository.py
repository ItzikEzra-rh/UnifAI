from storage.data_repository import DataRepository
from storage.data_repository import FileHandler
from pathlib import Path
import os


class FileDataRepository(DataRepository):
    def __init__(self, input_file_path, output_directory):
        self.input_file = FileHandler(input_file_path)

        # Derive other file names from the input file name
        base_name = Path(input_file_path).stem
        self.processed_file = FileHandler(os.path.join(output_directory, f"{base_name}_processed.json"))
        self.skipped_file = FileHandler(os.path.join(output_directory, f"{base_name}_skipped.json"))
        self.progress_file = FileHandler(os.path.join(output_directory, f"{base_name}_progress.json"))

    def load_data(self):
        return self.input_file.load_json()

    def save_processed_data(self, data):
        self.processed_file.save_json(data, indent=4)

    def save_progress(self, current_index):
        self.progress_file.save_json({"current_index": current_index})

    def save_skipped_data(self, data):
        self.skipped_file.save_json(data, indent=4)

    def load_progress(self):
        progress_data = self.progress_file.load_json(default_value={"current_index": 0})
        return progress_data.get('current_index', 0)

    def load_processed_data(self):
        return self.processed_file.load_json()

    def load_skipped_data(self):
        return self.skipped_file.load_json()
