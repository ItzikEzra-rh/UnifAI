from abc import ABC, abstractmethod
from resources.models import ResourceDoc


class ResourceRepository(ABC):
    @abstractmethod
    def save(self, doc: ResourceDoc) -> str:
        """Insert or replace a resource document."""
        ...

    @abstractmethod
    def get(self, rid: str) -> ResourceDoc:
        """Retrieve a resource document by ID."""
        ...

    @abstractmethod
    def delete(self, rid: str) -> None:
        """Delete a resource document by ID."""
        ...

    @abstractmethod
    def find_by_name(self, user_id: str, category: str, type: str, name: str) -> ResourceDoc | None:
        """Find a resource document by alias."""
        ...

    @abstractmethod
    def count(self, user_id: str, filter: dict) -> int:
        """Count documents matching a filter."""
        ...

    @abstractmethod
    def meta(self, rid: str) -> tuple[str, str]: ...

    @abstractmethod
    def count_nested(self, rid: str) -> int: ...

    @abstractmethod
    def exists(self, rid: str) -> bool: ...
