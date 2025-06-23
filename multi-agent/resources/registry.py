from datetime import datetime
from resources.models import ResourceDoc
from resources.repository.base import ResourceRepository
from blueprints.repository.repository import BlueprintRepository


class ResourcesRegistry:
    """Low-level CRUD + business rules (no Pydantic parsing)."""

    def __init__(
            self,
            repo: ResourceRepository,
            bp_repo: BlueprintRepository,  # for delete guard
    ):
        self._repo = repo
        self._bp_repo = bp_repo

    # ---------- write ----------
    def create(self, doc: ResourceDoc) -> ResourceDoc:
        # uniqueness guard
        if self._repo.find_by_name(doc.user_id, doc.category, doc.type, doc.name):
            raise ValueError(f"{doc.category}:{doc.type}:{doc.name} exists for user")
        self._repo.save(doc)
        return doc

    def update(self, rid: str, new_cfg: dict) -> ResourceDoc:
        doc = self._repo.get(rid)
        doc.config = new_cfg
        doc.version += 1
        doc.updated = datetime.utcnow()
        self._repo.save(doc)
        return doc

    def delete(self, rid: str) -> None:
        if self._bp_repo.count_usage(rid):
            raise RuntimeError("Resource is referenced by blueprints")
        self._repo.delete(rid)

    # ---------- read ----------
    def get(self, rid: str) -> ResourceDoc:
        return self._repo.get(rid)

    def raw_config(self, rid: str) -> dict:
        return self.get(rid).config
