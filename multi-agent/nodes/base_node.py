from abc import ABC, abstractmethod
from graph.step_context import StepContext
from graph.state.graph_state import GraphState
from core.types import StreamWriter
from typing import Optional, Any


class BaseNode(ABC):
    """
    • Stores StepContext / uid
    • Provides __call__ with streaming
    • NO domain-specific logic
    """

    def __init__(self, *, step_ctx: StepContext, name: str, **kwargs: Any):
        super().__init__(**kwargs)  # MRO
        self._ctx = step_ctx
        self.name = name
        self._stream_writer: Optional[StreamWriter] = None

    @abstractmethod
    def run(self, state: GraphState) -> GraphState:
        ...

    def __call__(self,
                 state: GraphState,
                 writer: StreamWriter = None) -> GraphState:
        self._stream_writer = writer
        result = self.run(state)
        self._stream({"node": self.uid,
                      "display_name": self.display_name,
                      "type": "complete",
                      "state": result})
        return result

    def _stream(self, payload: dict):
        if self._stream_writer:
            self._stream_writer(payload)

    @property
    def uid(self) -> str:
        return self._ctx.uid

    @property
    def display_name(self) -> str:
        return self._ctx.metadata.display_name
