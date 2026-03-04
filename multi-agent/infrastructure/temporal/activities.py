"""
Temporal activities — thin SDK wrappers.

Graph activities delegate to NodeExecutor for business logic.
Lifecycle activities delegate to SessionLifecycle for session
state transitions (complete / fail).
"""
from temporalio import activity

from engine.distributed.node_executor import NodeExecutor
from session.lifecycle import SessionLifecycle
from session.user_session_manager import UserSessionManager
from infrastructure.temporal.models import (
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
    """

    def __init__(self, node_executor: NodeExecutor) -> None:
        self._executor = node_executor

    @activity.defn(name="execute_graph_node")
    def execute_node(self, params: ExecuteNodeParams) -> dict:
        activity.logger.info(f"Executing node: {params.node_uid}")
        return self._executor.execute_node(
            node_uid=params.node_uid,
            node_blueprint=params.node_blueprint,
            step_context=params.step_context,
            state=params.state,
        )

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
