from typing import Optional, Type, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel


class BaseTool(ABC):
    """
    A reusable base class for LangChain-compatible tools.
    Subclass this and implement `run()` (and optionally `arun()`).
    """

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None

    def __init__(
            self,
            name: str,
            description: str,
            args_schema: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.description = description
        self.args_schema = args_schema

    @abstractmethod
    def run(
            self,
            *args: Any,
            **kwargs: Any
    ) -> Any:
        """
        Synchronous execution logic. Must be implemented by subclass.
        """
        raise NotImplementedError("run must be implemented by subclasses")

    async def arun(self, *args: Any, **kwargs: Any) -> int:
        # For asynchronous execution, we can just call run for now
        return self.run(*args, **kwargs)
