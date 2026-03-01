"""
Temporal activities for graph node execution.

Each activity rebuilds a single node from its mini-blueprint,
injects the real StepContext, runs it, and discards it.
Stateless — like a Flask handler. Any worker can execute any node.
"""
from temporalio import activity

from blueprints.models.blueprint import BlueprintSpec, StepMeta
from core.enums import ResourceCategory
from graph.models import StepContext, AdjacentNodes
from graph.state.graph_state import GraphState
from graph.topology.models import StepTopology
from session.workflow_session_factory import WorkflowSessionFactory
from temporal.graph_models import ExecuteNodeParams, EvaluateConditionParams


class GraphNodeActivities:
    """
    Stateless activity class for Temporal workers.

    Created once at worker startup with session_factory (shared infra).
    Each activity call builds a fresh node from the mini-blueprint
    in the params. No blueprint_id, no MongoDB lookups.
    """

    def __init__(self, session_factory: WorkflowSessionFactory) -> None:
        self._factory = session_factory

    @activity.defn(name="execute_graph_node")
    def execute_node(self, params: ExecuteNodeParams) -> dict:
        """
        Build ONE node from its mini-blueprint, inject context, run it.
        """
        # 1. Build node from mini-blueprint (only this node's deps)
        mini_bp = BlueprintSpec.model_validate(params.node_blueprint)
        rt_plan = self._factory.build_runtime_plan(mini_bp)
        step = rt_plan.get_step(params.node_uid)

        # 2. Inject the REAL context (from the full graph, built at compile time)
        if params.step_context:
            real_ctx = _deserialize_step_context(params.step_context)
            step.func.set_context(real_ctx)

        # 3. Run
        activity.logger.info(f"Executing node: {params.node_uid}")
        state = GraphState.deserialize(params.state)
        result = step.func(state, config={})
        return result.serialize()

    @activity.defn(name="evaluate_condition")
    def evaluate_condition(self, params: EvaluateConditionParams) -> str:
        """
        Build a condition from its mini-blueprint, inject context, run it.
        """
        mini_bp = BlueprintSpec.model_validate(params.condition_blueprint)
        registry = self._factory.build_session_registry(mini_bp)
        condition = registry.get_instance(ResourceCategory.CONDITION, params.condition_rid)

        # Inject the real StepContext (same context as the node that owns this condition)
        if params.step_context and hasattr(condition, 'set_context'):
            real_ctx = _deserialize_step_context(params.step_context)
            condition.set_context(real_ctx)

        activity.logger.info(f"Evaluating condition: {params.condition_rid}")
        state = GraphState.deserialize(params.state)
        return condition(state)


def _deserialize_step_context(data: dict) -> StepContext:
    """Reconstruct a StepContext from a serialized dict."""
    from core.models import ElementCard

    # Reconstruct AdjacentNodes from serialized cards (instance excluded)
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
