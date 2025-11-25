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

# ────────── Public Chat Sharing ──────────
    def enable_public_chat(self, blueprint_id: str) -> bool:
        """Enable public chat sharing for a blueprint by setting shared=True."""
        return self._repo.update_shared_field(blueprint_id=blueprint_id, shared=True)
    
    def disable_public_chat(self, blueprint_id: str) -> bool:
        """Disable public chat sharing for a blueprint by setting shared=False."""
        return self._repo.update_shared_field(blueprint_id=blueprint_id, shared=False)
    
    def is_public_chat_enabled(self, blueprint_id: str) -> bool:
        """Check if public chat is enabled for a blueprint (shared == True)."""
        try:
            doc = self._repo.load(blueprint_id)
            return doc.get("shared") is True
        except KeyError:
            return False

    def get_public_chat_info(self, blueprint_id: str, frontend_url: str = None) -> Dict[str, Any]:
        """
        Get public chat information including status and share link.
        
        :param blueprint_id: The blueprint ID
        :param frontend_url: Optional frontend URL for share link generation. 
                            If not provided, share_link will be None.
        :return: Dictionary with enabled status, share_link, and blueprint_id
        :raises KeyError: If blueprint doesn't exist
        """
        enabled = self.is_public_chat_enabled(blueprint_id)
        share_link = None
        if enabled and frontend_url:
            share_link = f"{frontend_url}/chat/{blueprint_id}"
        
        return {
            "enabled": enabled,
            "share_link": share_link,
            "blueprint_id": blueprint_id
        }