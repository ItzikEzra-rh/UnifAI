from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping


@dataclass(slots=True)
class ChatHistoryItem:
    session_id: str
    metadata: Dict[str, Any]
    started_at: str
    blueprint_id: str
    blueprint_exists: bool = True
    public_chat_enabled: bool = False  # Only relevant for sessions from public links (metadata.source == "public_link")

    @classmethod
    def from_doc(cls, doc: Mapping[str, Any], blueprint_exists: bool = True, public_chat_enabled: bool = False) -> "ChatHistoryItem":
        rc = doc.get("run_context", {})
        return cls(
            session_id=rc.get("run_id"),
            metadata=doc.get("metadata", {}),
            started_at=rc.get("started_at"),
            blueprint_id=doc.get("blueprint_id", ""),
            blueprint_exists=blueprint_exists,
            public_chat_enabled=public_chat_enabled
        )

    # optional helper
    def asdict(self) -> Dict[str, Any]:
        return asdict(self)
