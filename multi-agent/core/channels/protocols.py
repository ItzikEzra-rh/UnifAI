"""
Channel protocols - abstractions for session communication.

StreamEmitter: ABC for emitting data during graph execution
SessionChannel: ABC for session-scoped channels (emit, close, future: input)
ChannelFactory: ABC for creating session channels (infrastructure concern, not engine concern)
"""
from abc import ABC, abstractmethod
from typing import Any


class StreamEmitter(ABC):
    """
    Abstract base class for emitting data during graph execution.
    Implementations are infrastructure-specific (e.g., LangGraphEmitter, RedisEmitter).
    """
    
    @abstractmethod
    def emit(self, data: Any) -> None:
        """Emit a chunk of data."""
        ...
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if emission is possible."""
        ...


class SessionChannel(ABC):
    """
    Abstract base class for session-scoped communication channels.
    
    Current: Output only (emit)
    Future: Add request_input() for HITL
    """
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """The session this channel belongs to."""
        ...
    
    @abstractmethod
    def emit(self, data: Any) -> None:
        """Emit data to the channel."""
        ...
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if channel is active."""
        ...
    
    @abstractmethod
    def close(self) -> None:
        """Close the channel."""
        ...
    
    def supports_input(self) -> bool:
        """
        Check if this channel supports receiving input (HITL).
        Default: False. Override in RedisSessionChannel.
        """
        return False


class ChannelFactory(ABC):
    """
    Abstract factory for creating session-scoped streaming channels.

    This is an INFRASTRUCTURE concern, not an engine concern.
    The same factory (e.g., Redis) can serve any graph engine
    (LangGraph, Temporal, etc.). Injected into SessionExecutor
    by the AppContainer based on deployment configuration.
    """

    @abstractmethod
    def create(self, session_id: str) -> SessionChannel:
        """
        Create a new streaming channel for the given session.

        Args:
            session_id: Unique session identifier for this channel.

        Returns:
            A ready-to-use SessionChannel instance.
        """
        ...

