"""
data_handler.py

Defines the abstract DataHandler interface, which specifies how different
data formats should be read and appended.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List


class DataHandler(ABC):
    """
    Abstract interface for a data handler that supports:
      - Streaming or batch-wise reads
      - Appending new records
      - Resource management (if applicable)
    """

    @abstractmethod
    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream or batch-read data from the underlying source
        in a memory-efficient manner.

        :return: An iterator yielding records as dictionaries.
        """
        pass

    @abstractmethod
    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Append a single record to the underlying source.

        :param record: The record (dict) to append.
        """
        pass

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Append multiple records in one call.
        By default, it appends each record individually.
        Handlers can override this for efficiency.

        :param records: A list of record dicts to append.
        """
        for record in records:
            self.append_record(record)

    @abstractmethod
    def close(self) -> None:
        """
        Close any resources held by the handler.
        This can also be used to flush buffers, finalize file writes, etc.
        """
        pass

    def append_to_object(self, key: str, val: Any) -> None:
        """
        Optional: For JSON-like handlers to update a key-value pair in a top-level object.
        By default, raises NotImplementedError.
        """
        raise NotImplementedError("Not applicable for this handler.")

    def get_size(self) -> int:
        pass
