from typing import Any, Iterator

from engine.domain.base_executor import BaseGraphExecutor
from engine.domain.types import DEFAULT_RECURSION_LIMIT


class LangGraphExecutor(BaseGraphExecutor):
    """
    Wraps a LangGraph compiled graph (which has .invoke),
    exposing it as a BaseGraphExecutor with .run().
    """

    def __init__(
        self,
        compiled_graph: Any,
        recursion_limit: int = DEFAULT_RECURSION_LIMIT,
    ) -> None:
        self._compiled = compiled_graph
        self._recursion_limit = recursion_limit

    def run(self, initial_state: Any) -> Any:
        return self._compiled.invoke(
            initial_state,
            config={"recursion_limit": self._recursion_limit},
        )

    def stream(self, initial_state: Any, *args: Any, **kwargs: Any) -> Iterator[Any]:
        stream_mode = kwargs.get("stream_mode", None)
        if stream_mode:
            for chunk in self._compiled.stream(
                initial_state,
                stream_mode=stream_mode,
                config={"recursion_limit": self._recursion_limit},
            ):
                yield chunk

    def get_state(self) -> Any:
        return self._compiled.get_state(None)
