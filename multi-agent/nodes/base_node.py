from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from graph.graph_state import GraphState
StreamWriter = Callable[[Any], None]


class BaseNode(ABC):
    """
    Abstract base class for all graph nodes.
    Provides streaming-aware LLM invocation and unified node entrypoint.
    """

    def __init__(
            self,
            name: str,
            llm: Any = None,
            retriever: Any = None,
            tools: List[Any] = (),
            system_message: str = "",
            retries: int = 1,
    ):
        self.name = name
        self.llm = llm
        self.retriever = retriever
        self.tools = list(tools)
        self.system_message = system_message or ""
        self.retries = max(1, retries)
        self.stream_writer = None

    @abstractmethod
    def run(self, state: GraphState) -> GraphState:
        """
        Main execution logic, shared by run and stream.
        """
        ...

    def _done(self, result):
        if self.stream_writer:
            self.stream_writer({
                "node": self.name,
                "type": "complete",
                "state": result,
            })

    def __call__(self, state: GraphState, writer: StreamWriter = None) -> GraphState:
        """
        Unified entrypoint: stream if writer is passed, else run normally.
        """
        self.stream_writer = writer
        result = self.run(state)
        self._done(result)
        return result

    def call_llm(
            self,
            messages: List[Dict[str, str]],
            stream_event_type: str = "llm_token",
    ) -> str:
        """
        Calls LLM with messages. Streams chunks if writer is present.
        Returns full response.
        """
        if self.stream_writer:
            full = ""
            for chunk in self.llm.stream(messages):
                full += chunk
                self.stream_writer({
                    "node": self.name,
                    "type": stream_event_type,
                    "chunk": chunk,
                })
            return full
        else:
            return self.llm.chat(messages)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
