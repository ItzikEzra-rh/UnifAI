from typing import Protocol, Dict, Any


class BlueprintElementDef(Protocol):
    """
    Anything coming out of your Blueprint parser (LLMDef, ToolDef,
    RetrieverDef, NodeSpec, etc.) should conform to this:
      • .name:     str         – the instance key the user gave
      • .type:     str         – which plugin “type” to look up
      • .dict(...): Dict[str,Any] – raw config for Pydantic
    """
    name: str
    type: str

    def dict(self, *, exclude_unset: bool = ...) -> Dict[str, Any]: ...
