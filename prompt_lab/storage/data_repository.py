from abc import ABC, abstractmethod


class DataRepository(ABC):
    def __init__(self, project_id=None):
        self.project_id = project_id

    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def save_processed_data(self, data):
        pass

    @abstractmethod
    def save_progress(self, progress_data):
        pass

    @abstractmethod
    def load_progress(self):
        pass
