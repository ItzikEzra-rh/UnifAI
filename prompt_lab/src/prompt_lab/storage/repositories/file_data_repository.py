"""
file_data_repository.py

Implements FileDataRepository, which uses JSONFileHandler for
input, processed, skipped, and progress data in local JSON files.
"""

from storage import (DataRepository,
                     JSONFileHandler)


class FileDataRepository(DataRepository):
    """
    A repository that uses JSONFileHandler for everything:
      - input data
      - processed data
      - skipped data
      - progress data

    Each data category is stored in a separate JSON file.
    """

    def __init__(
            self,
            input_file_path: str,
            processed_file_path: str,
            skipped_file_path: str,
            progress_file_path: str
    ):
        """
        :param input_file_path:    Path to the JSON file for input data
        :param processed_file_path:Path to the JSON file for processed data
        :param skipped_file_path:  Path to the JSON file for skipped data
        :param progress_file_path: Path to the JSON file for progress data
        """
        # Instantiate a JSONFileHandler for each data category
        self.input_handler = JSONFileHandler(input_file_path)
        self.processed_handler = JSONFileHandler(processed_file_path)
        self.skipped_handler = JSONFileHandler(skipped_file_path)
        self.progress_handler = JSONFileHandler(progress_file_path)

    # ---------------------------
    # DataRepository interface
    # ---------------------------

    def load_data(self) -> Iterator[Dict[str, Any]]:
        """
        Read data from the input JSON file (treated as a JSON list).
        """
        return self.input_handler.read_data()

    def load_processed_data(self) -> Iterator[Dict[str, Any]]:
        """
        Read processed data from the processed JSON file.
        """
        return self.processed_handler.read_data()

    def load_skipped_data(self) -> Iterator[Dict[str, Any]]:
        """
        Read skipped data from the skipped JSON file.
        """
        return self.skipped_handler.read_data()

    def save_processed_data(self, data: Dict[str, Any]) -> None:
        """
        Append a processed record to the processed JSON file.
        """
        self.processed_handler.append_record(data)

    def save_skipped_data(self, data: Dict[str, Any]) -> None:
        """
        Append a skipped record to the skipped JSON file.
        """
        self.skipped_handler.append_record(data)

    def save_progress(self, uuid: str, value: str = "") -> None:
        """
        Store progress info, e.g., {"uuid": <uuid>, "value": <value>}.
        """
        record = {"uuid": uuid, "value": value}
        self.progress_handler.append_record(record)

    def load_progress(self) -> Iterator[Dict[str, Any]]:
        """
        Read progress data from the progress JSON file.
        """
        return self.progress_handler.read_data()

    def close(self) -> None:
        """
        No persistent file handles to close; JSONFileHandler does everything on-the-fly.
        """
        self.input_handler.close()
        self.processed_handler.close()
        self.skipped_handler.close()
        self.progress_handler.close()
