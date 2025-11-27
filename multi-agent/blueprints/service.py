from typing import Any, Dict, List, Mapping
from .models.blueprint import BlueprintSpec, BlueprintDraft
from .repository.repository import BlueprintRepository
from .resolver import BlueprintResolver
from core.ref import RefWalker


class BlueprintService:
    def __init__(self, repo: BlueprintRepository, resolver: BlueprintResolver):
        self._repo = repo
        self._resolver = resolver

    # ────────── Write ──────────
    def save_draft(self, *, user_id: str, draft_dict: dict) -> str:
        draft_bp = BlueprintDraft(**draft_dict)
        rid_refs = list(RefWalker.external_rids(draft_bp))
        return self._repo.save(user_id=user_id, spec=draft_bp, rid_refs=rid_refs)

    # ────────── Single-blueprint reads (ID is globally unique) ──────────
    def load_draft(self, blueprint_id: str) -> BlueprintDraft:
        doc = self._repo.load(blueprint_id)
        return BlueprintDraft(**doc["spec_dict"])

    def get_blueprint_draft_doc(self, blueprint_id: str) -> Mapping[str, Any]:
        """Get blueprint document with metadata for sharing operations."""
        return self._repo.load(blueprint_id)

    def get_blueprint_info(self, blueprint_id: str) -> Dict[str, Any]:
        """
        Get blueprint information including name and owner.
        
        :param blueprint_id: The blueprint ID
        :return: Dictionary with blueprint_id, blueprint_name, and owner_user_id
        :raises KeyError: If blueprint doesn't exist
        """
        draft = self.load_draft(blueprint_id)
        doc = self.get_blueprint_draft_doc(blueprint_id)
        
        return {
            "blueprint_id": blueprint_id,
            "blueprint_name": draft.name,
            "owner_user_id": doc.get("user_id", "")
        }

    def update_draft(self, *, blueprint_id: str, draft_dict: dict) -> bool:  # NEW
        draft = BlueprintDraft(**draft_dict)
        rid_refs = list(RefWalker.external_rids(draft))
        return self._repo.update(
            blueprint_id=blueprint_id, spec=draft, rid_refs=rid_refs
        )

    def load_resolved(self, blueprint_id: str) -> BlueprintSpec:
        return self._resolver.resolve(self.load_draft(blueprint_id))

    def load_draft_from_dict(self, draft_dict: dict) -> BlueprintDraft:
        """Load a BlueprintDraft from a dictionary without saving to database."""
        return BlueprintDraft(**draft_dict)

    def resolve_draft_dict(self, draft_dict: dict) -> BlueprintSpec:
        """Resolve a draft dictionary directly to BlueprintSpec without saving to database."""
        draft_bp = BlueprintDraft(**draft_dict)
        return self._resolver.resolve(draft_bp)

    def to_dict(self, blueprint_id: str) -> Dict[str, Any]:
        """Draft → JSON-serialisable dict (no meta)."""
        return self.load_draft(blueprint_id).model_dump(mode="json")

    def exists(self, blueprint_id: str) -> bool:
        return self._repo.exists(blueprint_id)

    def delete(self, blueprint_id: str) -> bool:
        return self._repo.delete(blueprint_id)

    # ────────── Bulk listing / counting (optionally per user) ──────────
    def list_ids(self, *, user_id: str | None = None, **pg) -> List[str]:
        return self._repo.list_ids(user_id=user_id, **pg)

    def list_draft_dicts(
            self, *, user_id: str | None = None, **pg
    ) -> List[Dict[str, Any]]:
        """
        Return pure-dict drafts (as saved) in one DB round-trip.
        """
        docs = self._repo.list_docs(user_id=user_id, **pg)
        return [doc["spec_dict"] for doc in docs]

    def list_draft_docs(
            self, *, user_id: str | None = None, **pg
    ) -> List[Mapping[str, Any]]:
        """
        Return pure-dict drafts (as saved) in one DB round-trip.
        """
        docs = self._repo.list_docs(user_id=user_id, **pg)
        return [doc for doc in docs]

    def list_resolved_docs(
            self, *, user_id: str | None = None, **pg
    ) -> List[Mapping[str, Any]]:
        """
        Return documents with resolved spec_dict instead of draft spec_dict.
        """
        docs = self._repo.list_docs(user_id=user_id, **pg)
        resolved_docs = []

        for doc in docs:
            try:
                # Create draft from spec_dict
                draft = BlueprintDraft(**doc["spec_dict"])
                # Resolve the draft to BlueprintSpec
                resolved_spec = self._resolver.resolve(draft)
                # Convert resolved spec to dict
                resolved_dict = resolved_spec.model_dump(mode="json")

                # Create new doc with resolved spec_dict
                resolved_doc = dict(doc)  # Copy all fields from original doc
                resolved_doc["spec_dict"] = resolved_dict  # Replace spec_dict with resolved version
                resolved_docs.append(resolved_doc)
            except Exception as e:
                # If resolution fails, skip this document
                continue

        return resolved_docs

    def count(self, *, user_id: str | None = None) -> int:
        return self._repo.count(user_id=user_id)

    @staticmethod
    def get_draft_schema() -> Dict[str, Any]:
        """
        Return the JSON schema of the BlueprintDraft model.
        """
        return BlueprintDraft.model_json_schema()

# ────────── Blueprint Public Usage Scope ──────────
    def set_public_usage_scope(self, blueprint_id: str, public_usage_scope: bool) -> bool:
        """
        Set the public_usage_scope (True/False) of a blueprint.
        
        :param blueprint_id: The blueprint ID
        :param public_usage_scope: True for public, False for private
        :return: True if the document was modified
        :raises KeyError: If blueprint doesn't exist
        :raises ValueError: If public_usage_scope is not a boolean
        """
        if not isinstance(public_usage_scope, bool):
            raise ValueError(f"public_usage_scope must be a boolean, got: {type(public_usage_scope)}")
        return self._repo.set_public_usage_scope(blueprint_id=blueprint_id, public_usage_scope=public_usage_scope)
    
    def get_public_usage_scope(self, blueprint_id: str) -> Dict[str, Any]:
        """
        Get the public_usage_scope of a blueprint.
        
        :param blueprint_id: The blueprint ID
        :return: Dictionary with public_usage_scope and blueprint_id
        :raises KeyError: If blueprint doesn't exist
        """
        doc = self._repo.load(blueprint_id)
        return {
            "public_usage_scope": doc.get("public_usage_scope", False),
            "blueprint_id": blueprint_id
        }
    
    def validate_blueprint(self, blueprint_id: str) -> Dict[str, Any]:
        """
        Validate a blueprint by resolving it and checking if it can be compiled.
        
        :param blueprint_id: The blueprint ID
        :return: Dictionary with validation result, blueprint info, and ownership details
        :raises KeyError: If blueprint doesn't exist
        """
        try:
            # Try to resolve the blueprint - this validates it can be loaded and resolved
            resolved = self.load_resolved(blueprint_id)
            
            # Get blueprint info
            info = self.get_blueprint_info(blueprint_id)
            
            return {
                "valid": True,
                "blueprint_id": blueprint_id,
                "blueprint_name": info["blueprint_name"],
                "owner_user_id": info["owner_user_id"]
            }
        except Exception as e:
            # If resolution fails, blueprint is invalid
            try:
                info = self.get_blueprint_info(blueprint_id)
                return {
                    "valid": False,
                    "error": str(e),
                    "blueprint_id": blueprint_id,
                    "blueprint_name": info.get("blueprint_name", ""),
                    "owner_user_id": info.get("owner_user_id", "")
                }
            except KeyError:
                # Blueprint doesn't exist
                return {
                    "valid": False,
                    "error": "Blueprint not found",
                    "blueprint_id": blueprint_id
                }