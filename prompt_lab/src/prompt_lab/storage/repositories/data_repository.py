from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, List, Set


class DataRepository(ABC):
    """Abstract class for a data repository interface."""

    # Input handler methods
    @abstractmethod
    def load_input_data(self) -> Iterator[Dict[str, Any]]:
        """Return the main data input in a streaming/iterative fashion."""
        pass

    @abstractmethod
    def get_input_size(self) -> int:
        """Return the size of the input data."""
        pass

    # Processed handler methods
    @abstractmethod
    def save_processed_data(self, data: List[Dict[str, Any]]) -> None:
        """Save the processed data."""
        pass

    @abstractmethod
    def load_processed_data_uuids(self) -> Set[str]:
        """Load and return a set of processed UUIDs."""
        pass

    # Skipped handler methods
    @abstractmethod
    def load_skipped_data(self) -> Iterator[Dict[str, Any]]:
        """Return the skipped data."""
        pass

    @abstractmethod
    def save_skipped_data(self, data: Dict[str, Any]) -> None:
        """Save the skipped data."""
        pass

    # Progress handler methods
    @abstractmethod
    def get_progress_data(self, progress_id: str) -> Dict[str, Any]:
        """Retrieve progress data by ID."""
        pass

    @abstractmethod
    def save_progress_data(self, progress_id: str, data: Dict[str, Any]) -> None:
        """Save or overwrite progress data by ID."""
        pass

    @abstractmethod
    def increment_progress(self, progress_id: str, key: str, amount: int) -> None:
        """Increment a specific progress key for a given progress ID."""
        pass

    # Resource management
    @abstractmethod
    def close(self) -> None:
        """Close all open resources."""
        pass
