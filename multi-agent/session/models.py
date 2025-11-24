from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class RuntimeElement:
    """Complete runtime element: instance + config + spec."""
    instance: Any
    config: Any
    spec: Any


@dataclass(slots=True)
class SessionMeta:
    title: str | None = None
    tags: Dict[str, str] = field(default_factory=dict)
    from_shared_link: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMeta":
        return cls(**data)
