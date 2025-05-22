from llms.chat.message import ChatMessage
from typing import Any


class LlmCapableMixin:
    """
    LlmCapableMixin requires the host class to implement:
    - `self._stream(dict)`
    - `self.uid: str`
    - `self.display_name: str`
    Typically provided by BaseNode.
    """

    def __init__(self, *, llm: Any, system_message: str = "", retries: int = 1, **kwargs: Any):
        super().__init__(**kwargs)  # MRO
        self.llm = llm
        self.system_message = system_message
        self.retries = max(1, retries)

    def _chat(self, messages: list[ChatMessage], *, event_type="llm_token") -> str:
        if getattr(self, "_stream_writer", None):
            out = ""
            for chunk in self.llm.stream(messages):
                out += chunk
                self._stream({"node": self.uid,
                              "name": self.display_name,
                              "type": event_type,
                              "chunk": chunk})
            return out
        return self.llm.chat(messages)
