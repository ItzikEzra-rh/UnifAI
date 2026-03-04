from typing import Any, Dict, Iterator, Optional

from core.channels import SessionChannel, ChannelFactory
from core.enums import ResourceCategory
from engine.domain.background_executor import BackgroundExecutor, ExecutionContext
from graph.state.graph_state import GraphState
from session.lifecycle import SessionLifecycle
from session.workflow_session import WorkflowSession


class SessionExecutor:
    """
    Orchestrates graph execution with session lifecycle hooks.

    Delegates lifecycle transitions (prepare / complete / fail) to
    SessionLifecycle.  Streaming channel management lives here because
    it is an execution concern, not a lifecycle concern.
    """

    def __init__(
        self,
        lifecycle: SessionLifecycle,
        channel_factory: ChannelFactory,
    ) -> None:
        self._lifecycle = lifecycle
        self._channel_factory = channel_factory

    def run(
        self,
        session: WorkflowSession,
        inputs: Dict[str, Any],
        scope: str = "public",
        logged_in_user: str = "",
    ) -> GraphState:
        self._lifecycle.prepare(session, inputs, scope, logged_in_user)
        try:
            final_state = session.executable_graph.run(session.graph_state)
        except Exception as e:
            self._lifecycle.fail(session, e)
            raise

        self._lifecycle.complete(session, final_state)
        return final_state

    def stream(
        self,
        session: WorkflowSession,
        inputs: Dict[str, Any],
        scope: str = "public",
        logged_in_user: str = "",
        **stream_kwargs: Any,
    ) -> Iterator[Any]:
        self._lifecycle.prepare(session, inputs, scope, logged_in_user)
        channel = self._channel_factory.create(session.get_run_id())
        self._inject_streaming(session, channel)

        try:
            for chunk in session.executable_graph.stream(
                session.graph_state,
                **stream_kwargs,
            ):
                yield chunk
                try:
                    session.graph_state = (
                        chunk[1].get("state")
                        if isinstance(chunk, (list, tuple)) and isinstance(chunk[1], dict)
                        else None
                    )
                except Exception as e:
                    raise e

            self._cleanup_streaming(session, channel)
            self._lifecycle.complete(session, session.graph_state)

        except GeneratorExit:
            self._cleanup_streaming(session, channel)
            self._lifecycle.complete(session, session.graph_state)
            raise
        except Exception as e:
            self._cleanup_streaming(session, channel)
            self._lifecycle.fail(session, e)
            raise

    def submit(
        self,
        session: WorkflowSession,
        inputs: Dict[str, Any],
        scope: str = "public",
        logged_in_user: str = "",
    ) -> str:
        """
        Fire-and-forget path for background executors (e.g. Temporal).

        Does NOT call lifecycle.prepare() here — the durable
        SessionWorkflow owns the entire lifecycle (prepare → execute →
        complete/fail) so there are no orphaned RUNNING sessions if the
        API process crashes between prepare and start.
        """
        executor = session.executable_graph
        if not isinstance(executor, BackgroundExecutor):
            raise TypeError(
                f"submit() requires a BackgroundExecutor, "
                f"got {type(executor).__name__}"
            )

        context = ExecutionContext(
            run_id=session.get_run_id(),
            inputs=inputs,
            scope=scope,
            logged_in_user=logged_in_user,
        )
        return executor.start(session.graph_state, context)

    # ------------------------------------------------------------------ #
    #  Streaming helpers (execution concern, not lifecycle concern)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _inject_streaming(session: WorkflowSession, channel: Optional[SessionChannel]) -> None:
        for node in session.session_registry.all_of(ResourceCategory.NODE).values():
            if hasattr(node, "set_streaming_channel"):
                node.set_streaming_channel(channel)

    @staticmethod
    def _cleanup_streaming(session: WorkflowSession, channel: SessionChannel) -> None:
        SessionExecutor._inject_streaming(session, None)
        channel.close()
