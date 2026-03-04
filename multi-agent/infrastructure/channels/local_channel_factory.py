"""
Local channel factory for same-process execution.

Creates LocalSessionChannel instances backed by LangGraphEmitter.
Suitable for development and single-process deployments.
"""
from core.channels import ChannelFactory, SessionChannel
from infrastructure.langgraph.emitter import LangGraphEmitter
from .local_channel import LocalSessionChannel


class LocalChannelFactory(ChannelFactory):
    """
    Factory that creates in-process streaming channels.

    Uses LangGraph's built-in stream writer for emission.
    Suitable for same-process execution (Flask direct mode).

    For cross-process engines (Temporal) or production deployments,
    use a Redis-based factory instead.
    """

    def create(self, session_id: str) -> SessionChannel:
        emitter = LangGraphEmitter()
        return LocalSessionChannel(
            session_id=session_id,
            emitter=emitter,
        )
