"""
Local channel factory for same-process execution.

Creates LocalSessionChannel instances backed by LangGraphEmitter.
Suitable for development and single-process deployments.
"""
from mas.core.channels import ChannelFactory, SessionChannel
from outbound.langgraph.emitter import LangGraphEmitter
from .channel import LocalSessionChannel


class LocalChannelFactory(ChannelFactory):

    def create(self, session_id: str) -> SessionChannel:
        emitter = LangGraphEmitter()
        return LocalSessionChannel(session_id=session_id, emitter=emitter)
