from typing import Any, Dict, Iterator, Optional, Union
from session.user_session_manager import UserSessionManager
from session.repository.repository import SessionRepository
from session.workflow_session import WorkflowSession
from graph.graph_state import GraphState
from core.context import set_current_context

SessionOrId = Union[WorkflowSession, str]


class SessionExecutor:
    """
    SRP: only handles “run” and “stream” of a WorkflowSession.
    Can accept either a WorkflowSession or a run_id string.
    """

    def __init__(
            self,
            session_manager: UserSessionManager,
            repository: SessionRepository
    ):
        self._sessions = session_manager
        self._repo = repository

    def _resolve_session(self, session_or_id: SessionOrId) -> WorkflowSession:
        """
        If given a WorkflowSession, return it.
        Otherwise treat it as run_id and load via the manager.
        """
        if isinstance(session_or_id, WorkflowSession):
            return session_or_id

        run_id = session_or_id
        session = self._sessions.get_session(run_id)
        return session

    def _pre_run(self, session: WorkflowSession, inputs: Dict[str, Any]) -> None:
        """
        1) bind RunContext into ContextVar
        2) seed input into the GraphState
        """
        set_current_context(session.run_context)
        session.graph_state.update(inputs)

    def _post_run(self, session: WorkflowSession, final_state: GraphState) -> None:
        """
        1) attach final state
        2) mark context finished
        3) re‐bind new context
        4) persist
        """
        session.graph_state = final_state
        session.run_context = session.run_context.mark_finished()
        set_current_context(session.run_context)
        self._repo.save(session)

    def run(
            self,
            session_or_id: SessionOrId,
            inputs: Dict[str, Any]
    ) -> GraphState:
        """
        Run the graph to completion and return the final GraphState.
        """
        session = self._resolve_session(session_or_id)
        self._pre_run(session, inputs)

        try:
            final_state = session.executable_graph.run(session.graph_state)
        except Exception as e:
            # delegate to node‐level logger if present
            # if getattr(session, "logger", None):
            #     session.logger.log_node_error("SessionExecutor", e)
            raise e

        self._post_run(session, final_state)
        return final_state

    def stream(
            self,
            session_or_id: SessionOrId,
            inputs: Dict[str, Any],
            **stream_kwargs: Any
    ) -> Iterator[Any]:
        """
        Stream execution chunks, then persist at the end.
        """
        session = self._resolve_session(session_or_id)
        self._pre_run(session, inputs)

        try:
            for chunk in session.executable_graph.stream(
                    session.graph_state,
                    **stream_kwargs
            ):
                yield chunk

        except Exception as e:
            # if getattr(session, "logger", None):
            #     session.logger.log_node_error("SessionExecutor", e)
            raise e

        # once the generator ends, finalize
        self._post_run(session, session.graph_state)
