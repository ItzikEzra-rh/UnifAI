from abc import ABC, abstractmethod


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
    def save_progress(self, uuid, value=""):
        pass

    @abstractmethod
    def load_progress(self):
        pass

    @abstractmethod
    def save_skipped_data(self, data):
        pass
