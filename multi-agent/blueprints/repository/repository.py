from abc import ABC, abstractmethod
from typing import List
from schemas.blueprint.blueprint import BlueprintSpec


class BlueprintRepository(ABC):
    @abstractmethod
    def save(self, spec: BlueprintSpec) -> str:
        """Persist the spec, returning a generated blueprint_id."""
        ...

    @abstractmethod
    def load(self, blueprint_id: str) -> BlueprintSpec:
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
    def count(self) -> int:
        """Return the total number of blueprints."""
        ...
