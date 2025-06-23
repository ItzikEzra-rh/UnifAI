from typing import Any, Dict, List
from .models.blueprint import BlueprintSpec, BlueprintDraft
from .repository.repository import BlueprintRepository
from .resolver import BlueprintResolver
from .serializers import blueprint_to_dict_with_meta


class BlueprintService:
    def __init__(self, repo: BlueprintRepository, resolver: BlueprintResolver):
        """ Initialize the BlueprintService with a repository and resolver. """
        self._repo = repo
        self._resolver = resolver

    def save_draft(self, user_id: str, draft_dict: dict) -> str:
        draft = BlueprintDraft(**draft_dict)
        return self._repo.save(user_id, draft)

    # Load & resolve ------------------------------------------------------
    def load_resolved(self, bp_id: str) -> BlueprintSpec:
        draft_dict = self._repo.load(bp_id)
        draft = BlueprintDraft(**draft_dict["spec_dict"])
        return self._resolver.resolve(draft)

    def to_dict(self, blueprint_id: str) -> Dict[str, Any]:
        spec = self.load_resolved(blueprint_id)
        return blueprint_to_dict_with_meta(spec)

    def list_ids(self, **pagination) -> List[str]:
        return self._repo.list_ids(**pagination)

    def list_models(self, **pagination) -> List[BlueprintSpec]:
        return self._repo.list_specs(**pagination)

    def list_dicts(self, **pagination) -> List[Dict[str, Any]]:
        return [{bid: self.to_dict(bid)} for bid in self.list_ids(**pagination)]

    def exists(self, blueprint_id: str) -> bool:
        return self._repo.exists(blueprint_id)

    def delete(self, blueprint_id: str) -> bool:
        return self._repo.delete(blueprint_id)

    def count(self) -> int:
        return self._repo.count()
