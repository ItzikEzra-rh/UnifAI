from typing import Protocol, runtime_checkable
from llms.chat.message import ChatMessage


@runtime_checkable
class _StreamProvider(Protocol):
    uid: str
    def _stream(self, payload: dict) -> None: ...


class LlmCapableMixin(_StreamProvider):
    def __init__(self, *, llm, system_message: str = "", retries: int = 1, **_):
        self.llm = llm
        self.system_message = system_message
        self.retries = max(1, retries)

    def _chat(self, messages: list[ChatMessage], *, event_type="llm_token") -> str:
        if getattr(self, "_stream_writer", None):
            out = ""
            for chunk in self.llm.stream(messages):
                out += chunk
                self._stream({"node": self.uid, "type": event_type, "chunk": chunk})
            return out
        return self.llm.chat(messages)
