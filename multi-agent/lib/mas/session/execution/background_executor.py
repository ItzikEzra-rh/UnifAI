"""
Reusable lifecycle operations for background session execution.

Encapsulates the business logic that every background engine needs:
get session → call lifecycle transition → close channel.

Adapters (Temporal activities, Celery tasks, etc.) delegate to this
class so they remain thin one-liner wrappers with zero business logic.
"""
from typing import Any, Dict, Optional

from mas.core.channels import ChannelFactory
from mas.session.execution.lifecycle import SessionLifecycle
from mas.session.management.user_session_manager import UserSessionManager


class BackgroundSessionExecutor:

    def __init__(
        self,
        session_manager: UserSessionManager,
        lifecycle: SessionLifecycle,
        channel_factory: Optional[ChannelFactory] = None,
    ) -> None:
        self._manager = session_manager
        self._lifecycle = lifecycle
        self._channel_factory = channel_factory

    def prepare(
        self,
        run_id: str,
        inputs: Dict[str, Any],
        scope: str,
        logged_in_user: str,
    ) -> dict:
        session = self._manager.get_session(run_id)
        self._lifecycle.prepare(session, inputs, scope, logged_in_user)
        return session.graph_state.serialize()

    def complete(self, run_id: str, final_state: dict) -> None:
        session = self._manager.get_session(run_id)
        self._lifecycle.complete(session, final_state)
        self._close_channel(run_id)

    def fail(self, run_id: str, error_message: str) -> None:
        session = self._manager.get_session(run_id)
        self._lifecycle.fail(session, RuntimeError(error_message))
        self._close_channel(run_id)

    def _close_channel(self, session_id: str) -> None:
        if self._channel_factory:
            channel = self._channel_factory.create(session_id)
            channel.close()
