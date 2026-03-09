"""
Local session channel for same-process execution.
Wraps a StreamEmitter for in-process streaming (Flask direct mode).
"""
from typing import Any, Optional
from mas.core.channels import SessionChannel, StreamEmitter


class LocalSessionChannel(SessionChannel):

    def __init__(self, session_id: str, emitter: Optional[StreamEmitter] = None):
        self._session_id = session_id
        self._emitter = emitter
        self._closed = False

    @property
    def session_id(self) -> str:
        return self._session_id

    def emit(self, data: Any) -> None:
        if self._closed:
            return
        if self._emitter and self._emitter.is_active():
            self._emitter.emit(data)

    def is_active(self) -> bool:
        if self._closed:
            return False
        return self._emitter is not None and self._emitter.is_active()

    def close(self) -> None:
        self._closed = True
