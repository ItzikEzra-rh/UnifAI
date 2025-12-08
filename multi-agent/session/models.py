from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class RuntimeElement:
    """Complete runtime element: instance + spec + resource_spec."""
    instance: Any
    spec: Any
    resource_spec: Any  # ResourceSpec with user-defined name, config, rid, type
    
    @property
    def config(self) -> Any:
        """Get config from resource_spec."""
        return self.resource_spec.config if self.resource_spec else None


@dataclass(slots=True)
class SessionMeta:
    title: str | None = None
    tags: Dict[str, str] = field(default_factory=dict)
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMeta":
        return cls(**data)
    
    @classmethod
    def model_validate(cls, data: Dict[str, Any] | "SessionMeta" | None) -> "SessionMeta":
        """
        Validate and create SessionMeta from dict or return existing instance.
        Mimics Pydantic's model_validate for compatibility with requirements.
        
        Args:
            data: Dict to validate, existing SessionMeta instance, or None
            
        Returns:
            SessionMeta instance
        """
        if data is None:
            return cls()
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            return cls(**data)
        raise ValueError(f"Cannot validate {type(data)} as SessionMeta")
