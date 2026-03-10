"""
Foreground (in-process) session execution with lifecycle orchestration.

Handles both blocking run() and streaming stream() paths.
The caller's thread stays engaged until execution completes.

WorkflowSession holds its SessionRecord by reference, so lifecycle
mutations to session.record are immediately visible on the session.
"""
from typing import Any, Dict, Iterator, Optional

from mas.core.channels import SessionChannel, ChannelFactory
from mas.core.enums import ResourceCategory
from mas.graph.state.graph_state import GraphState
from mas.session.execution.lifecycle import SessionLifecycle
from mas.session.domain.workflow_session import WorkflowSession


class ForegroundSessionRunner:
    """
    Orchestrates synchronous graph execution with session lifecycle hooks.

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
        self._lifecycle.prepare(session.record, inputs, scope, logged_in_user)

        try:
            final_state = session.executable_graph.run(session.graph_state)
        except Exception as e:
            self._lifecycle.fail(session.record, e)
            raise

        self._lifecycle.complete(session.record, final_state)
        return final_state

    def stream(
        self,
        session: WorkflowSession,
        inputs: Dict[str, Any],
        scope: str = "public",
        logged_in_user: str = "",
        **stream_kwargs: Any,
    ) -> Iterator[Any]:
        self._lifecycle.prepare(session.record, inputs, scope, logged_in_user)

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
            self._lifecycle.complete(session.record, session.graph_state)

        except GeneratorExit:
            self._cleanup_streaming(session, channel)
            self._lifecycle.complete(session.record, session.graph_state)
            raise
        except Exception as e:
            self._cleanup_streaming(session, channel)
            self._lifecycle.fail(session.record, e)
            raise

    @staticmethod
    def _inject_streaming(session: WorkflowSession, channel: Optional[SessionChannel]) -> None:
        for node in session.session_registry.all_of(ResourceCategory.NODE).values():
            if hasattr(node, "set_streaming_channel"):
                node.set_streaming_channel(channel)

    @staticmethod
    def _cleanup_streaming(session: WorkflowSession, channel: SessionChannel) -> None:
        ForegroundSessionRunner._inject_streaming(session, None)
        channel.close()
