from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator, List, Set


class DataRepository(ABC):
    """Abstract class for a data repository interface."""

    # Input handler methods
    @abstractmethod
    def load_input_data(self) -> Iterator[Dict[str, Any]]:
        """Return the main data input in a streaming/iterative fashion."""
        pass

    # Processed handler methods
    @abstractmethod
    def save_pass_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Save processed (passed) prompts."""
        pass

    @abstractmethod
    def save_fail_prompts(self, prompts: List[Dict[str, Any]]) -> None:
        """Save failed prompts."""
        pass

    # Stats handler methods
    @abstractmethod
    def update_retry_counter(self, count: int) -> None:
        """Update the retry counter in the stats."""
        pass

    @abstractmethod
    def update_prompt_generation_counter(self, count: int = 1) -> None:
        """Update the generation counter in the stats."""
        pass

    @abstractmethod
    def get_elements_size(self) -> int:
        pass

    @abstractmethod
    def set_elements_size(self, size) -> None:
        pass

    @abstractmethod
    def get_prompts_size(self) -> int:
        pass

    @abstractmethod
    def get_processed_num(self) -> int:
        pass

    @abstractmethod
    def set_prompts_size(self, size) -> None:
        pass

    # Output (Exporter) methods
    @abstractmethod
    def export(self) -> None:
        """Export processed data."""
        pass

    @abstractmethod
    def load_prompts_uuids(self) -> Set[str]:
        pass

    # Resource management
    @abstractmethod
    def close(self) -> None:
        """Close all open resources."""
        pass
