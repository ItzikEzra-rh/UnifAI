from abc import ABC, abstractmethod
from typing import List, Mapping, Any
from blueprints.models.blueprint import BlueprintSpec, BlueprintDraft


class BlueprintRepository(ABC):
    @abstractmethod
    def save(self, user_id, spec: BlueprintDraft) -> str:
        """Persist the spec, returning a generated blueprint_id."""
        ...

    @abstractmethod
    def load(self, blueprint_id: str) -> Mapping[str, Any]:
        """Load by blueprint_id (or raise KeyError)."""
        ...

    @abstractmethod
    def delete(self, blueprint_id: str) -> bool:
        """Delete by blueprint_id. Return True if something was removed."""
        ...

    @abstractmethod
    def exists(self, blueprint_id: str) -> bool:
        """Return True if that ID is in the store."""
        ...

    @abstractmethod
    def list_ids(self, skip: int = 0, limit: int = 100, sort_desc: bool = True) -> List[str]:
        """List all blueprint_ids, with pagination."""
        ...

    @abstractmethod
    def list_specs(self, skip: int = 0, limit: int = 100, sort_desc: bool = True) -> List[BlueprintSpec]:
        """List every BlueprintSpec, with pagination."""
        ...

    @abstractmethod
    def count_usage(self, rid: str) -> int:
        """Count how many blueprints reference a resource by its ID."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of blueprints."""
        ...
