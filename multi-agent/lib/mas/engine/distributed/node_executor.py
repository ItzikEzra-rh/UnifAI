"""
Stateless node execution logic for distributed engines.

Rebuilds a single node (or condition) from its mini-blueprint,
injects the real StepContext, runs it, and discards it.
Like a Flask handler — any worker can execute any node.

If a SessionChannel is provided, it is injected into the node
before execution so that background workers can stream events
to a distributed channel (Redis, Kafka, etc.).
"""
from typing import Any, Dict, Optional

from mas.blueprints.models.blueprint import BlueprintSpec, StepMeta
from mas.core.channels import SessionChannel
from mas.core.enums import ResourceCategory
from mas.graph.models import StepContext, AdjacentNodes
from mas.graph.state.graph_state import GraphState
from mas.graph.topology.models import StepTopology
from mas.session.building.workflow_session_factory import WorkflowSessionFactory


class NodeExecutor:
    """
    Stateless executor for individual graph nodes and conditions.

    Created once at worker startup with a shared session factory.
    Each call builds a fresh node from the mini-blueprint, injects
    context, runs it, and returns the result.
    """

    def __init__(self, session_factory: WorkflowSessionFactory) -> None:
        self._factory = session_factory

    def execute_node(
        self,
        node_uid: str,
        node_blueprint: Dict[str, Any],
        step_context: Dict[str, Any],
        state: Dict[str, Any],
        channel: Optional[SessionChannel] = None,
    ) -> dict:
        """
        Build ONE node from its mini-blueprint, inject context, run it.

        If a channel is provided, it is injected into the node so that
        streaming-capable nodes can emit events during execution.
        """
        mini_bp = BlueprintSpec.model_validate(node_blueprint)
        rt_plan = self._factory.build_runtime_plan(mini_bp)
        step = rt_plan.get_step(node_uid)

        if step_context:
            real_ctx = _deserialize_step_context(step_context)
            step.func.set_context(real_ctx)

        if channel and hasattr(step.func, "set_streaming_channel"):
            step.func.set_streaming_channel(channel)

        graph_state = GraphState.deserialize(state)
        result = step.func(graph_state, config={})
        return result.serialize()

    def evaluate_condition(
        self,
        condition_rid: str,
        condition_blueprint: Dict[str, Any],
        step_context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """
        Build a condition from its mini-blueprint, inject context, run it.
        """
        mini_bp = BlueprintSpec.model_validate(condition_blueprint)
        registry = self._factory.build_session_registry(mini_bp)
        condition = registry.get_instance(ResourceCategory.CONDITION, condition_rid)

        if step_context and hasattr(condition, 'set_context'):
            real_ctx = _deserialize_step_context(step_context)
            condition.set_context(real_ctx)

        graph_state = GraphState.deserialize(state)
        return condition(graph_state)


def _deserialize_step_context(data: dict) -> StepContext:
    """Reconstruct a StepContext from a serialized dict."""
    from mas.core.models import ElementCard

    adjacent_data = data.get("adjacent_nodes", {})
    nodes_dict = {}
    for uid, card_dict in adjacent_data.get("nodes", {}).items():
        nodes_dict[uid] = ElementCard(
            uid=card_dict.get("uid", uid),
            category=ResourceCategory(card_dict.get("category", "nodes")),
            type_key=card_dict.get("type_key", ""),
            name=card_dict.get("name", ""),
            description=card_dict.get("description", ""),
            capabilities=set(card_dict.get("capabilities", [])),
            reads=set(card_dict.get("reads", [])),
            writes=set(card_dict.get("writes", [])),
            instance=None,
            config=card_dict.get("config"),
            skills=card_dict.get("skills", {}),
            metadata=card_dict.get("metadata"),
        )

    return StepContext(
        uid=data.get("uid", ""),
        metadata=StepMeta.model_validate(data.get("metadata", {})),
        adjacent_nodes=AdjacentNodes(nodes=nodes_dict),
        branches=data.get("branches", {}),
        topology=StepTopology.model_validate(data.get("topology", {})),
    )
