from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator


class DataRepository(ABC):
    """Abstract class for a data repository interface."""

    @abstractmethod
    def input_load_data(self) -> Iterator[Dict[str, Any]]:
        """Return the main data input in a streaming/iterative fashion."""
        pass

    @abstractmethod
    def load_processed_data(self) -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_skipped_data(self) -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_processed_data(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def save_progress(self, uuid: str, value: str = "") -> None:
        pass

    @abstractmethod
    def load_progress(self) -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_skipped_data(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_input_size(self) -> int:
        pass

    @abstractmethod
    def close(self) -> None:
        """Close all open resources."""
        pass
