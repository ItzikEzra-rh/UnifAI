from typing import Any, Dict, Iterator, List, Tuple
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ConfigDict


def append_dict_to_list(existing: List[Dict[str, Any]], new_item) -> List[Dict[str, Any]]:
    """
    Merge strategy for `nodes_output`:
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


class GraphState(BaseModel):
    """
    Pydantic‐backed execution state for LangGraph.

    • Declares your main channels with merge‐strategies via Annotated
    • Allows arbitrary extra keys at runtime (extra="allow")
    • Behaves like a dict: __getitem__, __setitem__, keys(), items(), etc.
    """
    model_config = ConfigDict(
        extra="allow",  # permit new keys on the fly
        arbitrary_types_allowed=True  # in case you store non‐JSON types
    )

    # —————– Channels (with merge strategies) —————–
    # last‐writer‐wins for user_prompt:
    user_prompt: Annotated[str, lambda old, new: new] = ""
    # accumulate dicts into a list:
    nodes_output: Annotated[List[Dict[str, Any]], append_dict_to_list] = Field(default_factory=list)
    # last‐writer‐wins for output:
    output: Annotated[str, lambda old, new: new] = ""

    # —————– Helpers to access Pydantic “extras” —————–
    @property
    def _extra(self) -> Dict[str, Any]:
        return getattr(self, "__pydantic_extra__", {}) or {}

    # —————– Dict‐like API —————–
    def __getitem__(self, key: str) -> Any:
        if key in self.__class__.model_fields:
            return getattr(self, key)
        if key in self._extra:
            return self._extra[key]
        raise KeyError(f"{key!r} not found in state.")

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.__class__.model_fields:
            setattr(self, key, value)
        else:
            # store in extras
            self._extra[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self.__class__.model_fields:
            delattr(self, key)
        elif key in self._extra:
            del self._extra[key]
        else:
            raise KeyError(f"{key!r} not found in state.")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self[k] = v

    def keys(self) -> Iterator[str]:
        return iter(list(self.__class__.model_fields.keys()) + list(self._extra.keys()))

    def items(self) -> Iterator[Tuple[str, Any]]:
        for k in self.__class__.model_fields:
            yield k, getattr(self, k)
        for k, v in self._extra.items():
            yield k, v

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Override Pydantic’s `model_dump()` to include both
        declared fields and dynamic extras.
        """
        base = super().model_dump(*args, **kwargs)
        # extras already held in __pydantic_extra__
        return {**base, **self._extra}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dict()})"
