import json
import os
from storage.data_repository import DataRepository


class FileDataRepository(DataRepository):
    def __init__(self, file_path, progress_file=None):
        super().__init__()
        self.file_path = file_path
        self.progress_file = progress_file or file_path.replace('.json', '_progress.json')
        self.processed_file = file_path.replace('.json', '_processed.json')

    def load_data(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def save_processed_data(self, data):
        with open(self.processed_file, 'w') as file:
            json.dump(data, file, indent=4)

    def save_progress(self, current_index):
        progress_data = {"current_index": current_index}
        with open(self.progress_file, 'w') as file:
            json.dump(progress_data, file)

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as file:
                progress_data = json.load(file)
                return progress_data.get('current_index', 0)
        return 0
