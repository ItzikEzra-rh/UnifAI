from typing import Any, Dict, Iterator, Tuple
from pydantic import BaseModel, ConfigDict


class BaseGraphState(BaseModel):
    """
    Base class for graph execution state.
    Implements dict-like API; allows extra fields.
    """
    model_config = ConfigDict(extra="allow")

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        delattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            setattr(self, k, v)

    def keys(self) -> Iterator[str]:
        return iter(self.__dict__.keys())

    def items(self) -> Iterator[Tuple[str, Any]]:
        return iter(self.__dict__.items())

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        # override Pydantic’s dict() to return exactly our internal dict
        return dict(self.__dict__)
