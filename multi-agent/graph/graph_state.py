from typing import Any, Dict, Iterator, List, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ConfigDict


def append_dict_to_list(existing: List[Dict[str, Any]], new_item) -> List[Dict[str, Any]]:
    """
    Merge strategy for nodes_output:
    - Keeps existing list
    - Flattens if new_item is a list
    - Appends a dict if not already present
    """
    if not isinstance(existing, list):
        existing = []

    if isinstance(new_item, list):
        out = existing
        for single in new_item:
            out = append_dict_to_list(out, single)
        return out

    if not isinstance(new_item, dict):
        return existing

    if new_item in existing:
        return existing

    return existing + [new_item]


def merge_dynamic_fields(existing: Dict[str, Any], new_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge strategy for dynamic_fields:
    - Starts with existing dictionary
    - Updates with new values
    """
    merged = existing.copy() if existing else {}
    if isinstance(new_values, dict):
        merged.update(new_values)
    return merged


class GraphState(BaseModel):
    """
    Pydantic-backed execution state for LangGraph.

    • Declares your main channels with merge-strategies via Annotated
    • Allows arbitrary extra keys at runtime (extra="allow")
    • Behaves like a dict: __getitem__, __setitem__, keys(), items(), etc.
    • Properly handles state persistence across LangGraph nodes
    • Raises KeyError for non-existent keys (like standard dict)
    """
    model_config = ConfigDict(
        extra="allow",  # permit new keys on the fly
        arbitrary_types_allowed=True  # in case you store non‐JSON types
    )

    # —————– Channels (with merge strategies) —————–
    # last-writer-wins for user_prompt:
    user_prompt: Annotated[str, lambda old, new: new] = ""
    # accumulate dicts into a list:
    nodes_output: Annotated[List[Dict[str, Any]], append_dict_to_list] = Field(default_factory=list)
    # last-writer-wins for output:
    output: Annotated[str, lambda old, new: new] = ""

    # Dynamic storage for extra fields (will be included in serialization)
    dynamic_fields: Annotated[Dict[str, Any], merge_dynamic_fields] = Field(default_factory=dict)

    # —————– Dict-like API —————–
    def __getitem__(self, key: str) -> Any:
        # 1) declared field?
        if key in self.__class__.model_fields:
            return getattr(self, key)
        # 2) dynamic field?
        if key in self.dynamic_fields:
            return self.dynamic_fields[key]
        # 3) not found anywhere - raise KeyError
        raise KeyError(f"{key!r} not found in state.")

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.__class__.model_fields:
            setattr(self, key, value)
        else:
            # Store in dynamic_fields which is preserved during serialization
            self.dynamic_fields[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self.__class__.model_fields:
            delattr(self, key)
        elif key in self.dynamic_fields:
            del self.dynamic_fields[key]
        else:
            raise KeyError(f"{key!r} not found in state.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Safe dictionary-like get method that doesn't raise KeyError
        """
        if key in self.__class__.model_fields:
            return getattr(self, key)
        return self.dynamic_fields.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self[k] = v

    def keys(self) -> Iterator[str]:
        return iter(list(self.__class__.model_fields.keys()) + list(self.dynamic_fields.keys()))

    def items(self) -> Iterator[Tuple[str, Any]]:
        for k in self.__class__.model_fields:
            yield k, getattr(self, k)
        for k, v in self.dynamic_fields.items():
            yield k, v

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Override Pydantic's model_dump() to include both
        declared fields and dynamic extras.
        """
        base = super().model_dump(*args, **kwargs)
        # Remove dynamic_fields from base if present to avoid duplication
        if "dynamic_fields" in base:
            base.pop("dynamic_fields")
        return {**base, **self.dynamic_fields}

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Override Pydantic's model_dump() for compatibility
        """
        return self.dict(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dict()})"
