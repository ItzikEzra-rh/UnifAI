from typing import Any, Dict, Iterator
from session.user_session_manager import UserSessionManager
from session.session_executor import SessionExecutor
from schemas.blueprint.blueprint import BlueprintSpec


class SessionService:
    """
    A service to handle session lifecycle: creation, execution, streaming, and listing.
    """

    def __init__(self, manager: UserSessionManager, executor: SessionExecutor):
        self._manager = manager
        self._executor = executor

    def create(self, user_id: str, blueprint_spec: BlueprintSpec, metadata: Dict[str, Any] = None) -> Any:
        """
        Create a new session and return its object (with run_id).
        """
        return self._manager.create_session(
            user_id=user_id,
            blueprint_spec=blueprint_spec,
            metadata=metadata or {}
        )

    def run(self, session_or_id: Any, inputs: Dict[str, Any]) -> Any:
        """
        Execute the session to completion, returning the final result.
        """
        return self._executor.run(
            session_or_id=session_or_id,
            inputs=inputs or {}
        )

    def stream(self, session_or_id: Any, inputs: Dict[str, Any], stream_mode: list = None) -> Iterator[Any]:
        """
        Execute the session in streaming mode, yielding chunks.
        """
        return self._executor.stream(
            session_or_id=session_or_id,
            inputs=inputs or {},
            stream_mode=stream_mode
        )

    def execute(self, session_or_id: Any, inputs: Dict[str, Any], stream: bool = False,
                stream_mode: list = None) -> Any:
        """
        Execute an existing session by run_id or session object.

        :param session_or_id: Session object or run_id.
        :param inputs: Input data for execution.
        :param stream: Whether to stream output.
        :param stream_mode: List of modes for streaming.
        :return: Final result or iterator of chunks.
        """
        if stream:
            return self.stream(session_or_id=session_or_id, inputs=inputs, stream_mode=stream_mode)
        return self.run(session_or_id=session_or_id, inputs=inputs)

    def list_for_user(self, user_id: str) -> list:
        """
        List all sessions created by a user.
        """
        return self._manager.list_sessions(user_id)

    def get(self, run_id: str) -> Any:
        """
        Fetch a session object by its run_id.
        """
        return self._manager.get_session(run_id)
