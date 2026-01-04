from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping, Optional
from pydantic import BaseModel, field_validator
from .models import SessionMeta


class CreateSessionRequest(BaseModel):
    """Request DTO for session creation with automatic metadata validation."""
    user_id: str
    blueprint_id: str
    metadata: SessionMeta | None = None

    @field_validator("metadata", mode="before")
    @classmethod
    def cast_metadata(cls, v):
        """Let Pydantic handle the union resolution automatically."""
        if v is None:
            return SessionMeta()
        if isinstance(v, dict):
            return SessionMeta.model_validate(v)
        return v


@dataclass(slots=True)
class ChatHistoryItem:
    session_id: str
    metadata: Dict[str, Any]
    started_at: str
    blueprint_id: str
    blueprint_exists: bool = True

    @classmethod
    def from_doc(cls, doc: Mapping[str, Any], blueprint_exists: bool = True, public_usage_scope: bool = False) -> "ChatHistoryItem":
        rc = doc.get("run_context", {})
        metadata = dict(doc.get("metadata", {}))
        metadata["public_usage_scope"] = public_usage_scope
        return cls(
            session_id=rc.get("run_id"),
            metadata=metadata,
            started_at=rc.get("started_at"),
            blueprint_id=doc.get("blueprint_id", ""),
            blueprint_exists=blueprint_exists
        )

    # optional helper
    def asdict(self) -> Dict[str, Any]:
        return asdict(self)
