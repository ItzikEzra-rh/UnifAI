"""
Node deployment serializer for distributed execution.

Extracts mini-blueprints and serialized StepContext from RTGraphPlan
so that a remote worker can rebuild and execute a single node without
the full blueprint or live graph.
"""
from typing import Any, Dict, Optional, Set, Tuple

from mas.core.enums import ResourceCategory
from mas.session.domain.session_registry import SessionRegistry
from mas.graph.models.workflow import RTStep


class NodeDeploymentSerializer:
    """
    Responsible for preparing deployment payloads (mini-blueprints,
    step contexts) from runtime plan data.

    Separates deployment concerns from graph planning (SRP).
    """

    def __init__(self, session_registry: SessionRegistry) -> None:
        self._session = session_registry

    def serialize_node_blueprint(self, step: RTStep) -> Dict[str, Any]:
        """
        Return a serialized mini BlueprintSpec containing ONLY the
        resources this node needs (its LLM, providers, tools, etc.).
        """
        from mas.blueprints.models.blueprint import BlueprintSpec, StepDef
        from mas.core.ref.models import NodeRef

        node_elem = self._session.get(ResourceCategory.NODE, step.rid)
        node_spec = node_elem.resource_spec
        dep_rids = _collect_refs(node_spec.config.model_dump(mode="json"))

        llms, providers, tools, retrievers = [], [], [], []
        for rid in dep_rids:
            found = self._find_resource_spec(rid)
            if found is None:
                continue
            category, spec = found
            if category == ResourceCategory.LLM:
                llms.append(spec)
            elif category == ResourceCategory.PROVIDER:
                providers.append(spec)
            elif category == ResourceCategory.TOOL:
                tools.append(spec)
            elif category == ResourceCategory.RETRIEVER:
                retrievers.append(spec)

        mini_bp = BlueprintSpec(
            providers=providers,
            llms=llms,
            tools=tools,
            retrievers=retrievers,
            nodes=[node_spec],
            conditions=[],
            plan=[StepDef(uid=step.uid, node=NodeRef(node_spec.rid.root))],
            name="mini",
            description="",
        )
        return mini_bp.model_dump(mode="json")

    def serialize_condition_blueprint(self, condition_rid: str) -> Dict[str, Any]:
        """
        Return a serialized mini BlueprintSpec for a condition.
        Conditions are typically lightweight (no LLM, no tools).
        """
        from mas.blueprints.models.blueprint import BlueprintSpec

        cond_elem = self._session.get(ResourceCategory.CONDITION, condition_rid)
        cond_spec = cond_elem.resource_spec

        mini_bp = BlueprintSpec(
            providers=[],
            llms=[],
            tools=[],
            retrievers=[],
            nodes=[],
            conditions=[cond_spec],
            plan=[],
            name="mini",
            description="",
        )
        return mini_bp.model_dump(mode="json")

    def serialize_step_context(self, step: RTStep) -> Dict[str, Any]:
        """
        Return the serialized StepContext for this node.

        Built from the FULL graph topology (adjacent nodes, finalizer
        distances, etc.) at compile time.
        """
        ctx = step.func._ctx
        if ctx is None:
            return {}

        return {
            "uid": ctx.uid,
            "metadata": ctx.metadata.model_dump(mode="json") if hasattr(ctx.metadata, 'model_dump') else {},
            "adjacent_nodes": _serialize_adjacent_nodes(ctx.adjacent_nodes),
            "branches": dict(ctx.branches),
            "topology": ctx.topology.model_dump(mode="json") if hasattr(ctx.topology, 'model_dump') else {},
        }

    def _find_resource_spec(self, rid: str) -> Optional[Tuple[ResourceCategory, Any]]:
        """Look up a rid across all resource categories."""
        for category in ResourceCategory:
            try:
                elem = self._session.get(category, rid)
                return category, elem.resource_spec
            except (KeyError, IndexError):
                continue
        return None


def _collect_refs(obj: Any) -> Set[str]:
    """Recursively collect all $ref: rids from a serialized config."""
    refs: Set[str] = set()
    if isinstance(obj, dict):
        for v in obj.values():
            refs.update(_collect_refs(v))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            refs.update(_collect_refs(item))
    elif isinstance(obj, str) and obj.startswith("$ref:"):
        refs.add(obj[5:])
    return refs


def _serialize_adjacent_nodes(adjacent_nodes) -> Dict[str, Any]:
    """
    Serialize AdjacentNodes, EXCLUDING live instance references.

    ElementCard has `instance: Any` which holds the live node object.
    This can't be serialized. We extract only the serializable fields.
    """
    from dataclasses import fields as dc_fields

    serialized_nodes = {}
    for uid, card in adjacent_nodes.nodes.items():
        card_dict = {}
        for f in dc_fields(card):
            if f.name == "instance":
                continue
            value = getattr(card, f.name)
            if isinstance(value, set):
                card_dict[f.name] = list(value)
            elif hasattr(value, 'model_dump'):
                card_dict[f.name] = value.model_dump(mode="json")
            elif hasattr(value, 'value'):
                card_dict[f.name] = value.value
            else:
                card_dict[f.name] = value
        serialized_nodes[uid] = card_dict
    return {"nodes": serialized_nodes}
