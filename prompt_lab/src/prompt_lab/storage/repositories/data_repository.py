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

    # Processed (Pass) handler methods
    @abstractmethod
    def save_pass_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Save processed (passed) prompts."""
        pass

    @abstractmethod
    def load_pass_prompts_uuids(self) -> Set[str]:
        """Load and return a set of processed (passed) UUIDs."""
        pass

    # Failed handler methods
    @abstractmethod
    def save_fail_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Save failed prompts."""
        pass

    # Stats handler methods
    @abstractmethod
    def update_retry_counter(self, count: int) -> None:
        """Update the retry counter in the stats."""
        pass

    # Output (Exporter) methods
    @abstractmethod
    def export(self) -> None:
        """Export processed data."""
        pass

    # Resource management
    @abstractmethod
    def close(self) -> None:
        """Close all open resources."""
        pass
