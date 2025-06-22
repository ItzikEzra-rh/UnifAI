from datetime import datetime
from resources.models import ResourceDoc
from resources.repository.base import ResourceRepository


class ResourcesRegistry:
    """
    *Enforces* business rules:
      • alias uniqueness per (user id, category, type)
      • optimistic version bump on edits
      • “cannot delete while referenced” guard
    """

    def __init__(self, repo: ResourceRepository, bp_repo):
        self.repo = repo
        self.bp_repo = bp_repo  # injected BlueprintRepository

    # ---------- write ----------
    def create(self, user_id: str, category: str, type: str, name: str, cfg_dict: dict) -> ResourceDoc:
        if self.repo.find_by_name(user_id, category, type, name):
            raise ValueError(f"{category}:{type}:{name} already exists for user")
        doc = ResourceDoc(user_id=user_id,
                          category=category,
                          type=type,
                          name=name,
                          cfg_dict=cfg_dict,
                          version=1)
        self.repo.save(doc)
        return doc

    def update(self, rid: str, cfg_dict) -> ResourceDoc:
        doc = self.repo.get(rid)
        doc.config = cfg_dict
        doc.version += 1
        doc.updated = datetime.utcnow()
        self.repo.save(doc)
        return doc

    def delete(self, rid: str):
        if self.bp_repo.count_usage(rid) > 0:
            raise RuntimeError("Resource still referenced by blueprints")
        self.repo.delete(rid)

    # ---------- read ----------
    def resolve(self, rid: str) -> dict:
        """Return *current* config dict; caller turns it into Pydantic model."""
        return self.repo.get(rid).config

    def get(self, rid: str) -> ResourceDoc:
        """Return the resource document."""
        return self.repo.get(rid)
