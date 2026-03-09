"""
Channel protocols — abstractions for session communication.

SessionChannel:       Write side — nodes emit events during execution.
SessionChannelReader: Read side  — subscribe endpoint consumes events.
ChannelFactory:       Creates writers and (optionally) readers.
StreamEmitter:        Low-level emission abstraction (LangGraph, etc.).
"""
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional


class StreamEmitter(ABC):
    """Low-level emission abstraction for engine-specific streaming."""

    @abstractmethod
    def emit(self, data: Any) -> None: ...

    @abstractmethod
    def is_active(self) -> bool: ...


class SessionChannel(ABC):
    """
    Write side of a session channel — used by nodes to emit events.

    Future: add request_input() for HITL.
    """

    @property
    @abstractmethod
    def session_id(self) -> str: ...

    @abstractmethod
    def emit(self, data: Any) -> None: ...

    @abstractmethod
    def is_active(self) -> bool: ...

    @abstractmethod
    def close(self) -> None: ...

    def supports_input(self) -> bool:
        return False


class SessionChannelReader(ABC):
    """
    Read side of a session channel — used by the subscribe endpoint
    to consume events.

    Implementations must be iterable.  Each iteration yields either:
      - a dict  → an actual event (exactly as emitted by the node)
      - None    → no new data (timeout); callers can use this for keepalives

    The iterator stops (returns) when the channel is closed.
    Data is never modified — what the node emits is what the reader yields.
    """

    @property
    @abstractmethod
    def session_id(self) -> str: ...

    @abstractmethod
    def __iter__(self) -> Iterator[Optional[dict]]: ...

    @abstractmethod
    def close(self) -> None: ...


class ChannelFactory(ABC):
    """
    Abstract factory for session-scoped streaming channels.

    Creates writers (always) and readers (when the backend supports
    cross-process communication, e.g. Redis).
    """

    @abstractmethod
    def create(self, session_id: str) -> SessionChannel:
        """Create a write channel for the given session."""
        ...

    def create_reader(self, session_id: str) -> Optional[SessionChannelReader]:
        """
        Create a read channel for the given session.

        Returns None when the backend does not support cross-process
        reading (e.g. LocalChannelFactory).
        """
        return None

