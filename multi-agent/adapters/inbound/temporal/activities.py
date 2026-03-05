"""
Temporal activities — inbound adapter (thin SDK wrappers).

Graph activities delegate to NodeExecutor for business logic.
Lifecycle activities delegate to SessionLifecycle for session
state transitions (complete / fail).

If a ChannelFactory is provided at worker startup, node activities
create a session-scoped channel and inject it into each node so
that background execution can stream events to a distributed bus
(Redis, Kafka, etc.).  When no factory is configured, nodes execute
without streaming — the behavior is identical to before.
"""
from typing import Optional

from temporalio import activity

from mas.core.channels import ChannelFactory
from mas.engine.distributed.node_executor import NodeExecutor
from mas.session.execution.lifecycle import SessionLifecycle
from mas.session.management.user_session_manager import UserSessionManager
from outbound.temporal.models import (
    ExecuteNodeParams,
    EvaluateConditionParams,
    PrepareSessionParams,
    CompleteSessionParams,
    FailSessionParams,
)


class GraphNodeActivities:
    """
    Stateless activity class for graph node/condition execution.

    Created once at worker startup. Each activity call delegates
    to NodeExecutor which builds a fresh node from the mini-blueprint.

    An optional ChannelFactory enables streaming from background
    workers.  When provided, a channel is created per node execution
    and injected into the rebuilt node.
    """

    def __init__(
        self,
        node_executor: NodeExecutor,
        channel_factory: Optional[ChannelFactory] = None,
    ) -> None:
        self._executor = node_executor
        self._channel_factory = channel_factory

    @activity.defn(name="execute_graph_node")
    def execute_node(self, params: ExecuteNodeParams) -> dict:
        activity.logger.info(f"Executing node: {params.node_uid}")

        channel = None
        if self._channel_factory and params.session_id:
            channel = self._channel_factory.create(params.session_id)

        try:
            return self._executor.execute_node(
                node_uid=params.node_uid,
                node_blueprint=params.node_blueprint,
                step_context=params.step_context,
                state=params.state,
                channel=channel,
            )
        finally:
            if channel:
                channel.close()

    @activity.defn(name="evaluate_condition")
    def evaluate_condition(self, params: EvaluateConditionParams) -> str:
        activity.logger.info(f"Evaluating condition: {params.condition_rid}")
        return self._executor.evaluate_condition(
            condition_rid=params.condition_rid,
            condition_blueprint=params.condition_blueprint,
            step_context=params.step_context,
            state=params.state,
        )


class SessionLifecycleActivities:
    """
    Activities for session lifecycle transitions.

    Called by SessionWorkflow (parent workflow) to complete or fail
    a session after the GraphTraversalWorkflow finishes.
    """

    def __init__(
        self,
        session_manager: UserSessionManager,
        lifecycle: SessionLifecycle,
    ) -> None:
        self._manager = session_manager
        self._lifecycle = lifecycle

    @activity.defn(name="prepare_session")
    def prepare_session(self, params: PrepareSessionParams) -> dict:
        """Seed inputs, mark RUNNING, persist. Returns the seeded state."""
        activity.logger.info(f"Preparing session: {params.run_id}")
        session = self._manager.get_session(params.run_id)
        self._lifecycle.prepare(
            session, params.inputs, params.scope, params.logged_in_user,
        )
        return session.graph_state.serialize()

    @activity.defn(name="complete_session")
    def complete_session(self, params: CompleteSessionParams) -> None:
        activity.logger.info(f"Completing session: {params.run_id}")
        session = self._manager.get_session(params.run_id)
        self._lifecycle.complete(session, params.final_state)

    @activity.defn(name="fail_session")
    def fail_session(self, params: FailSessionParams) -> None:
        activity.logger.info(f"Failing session: {params.run_id}")
        session = self._manager.get_session(params.run_id)
        self._lifecycle.fail(session, RuntimeError(params.error_message))
