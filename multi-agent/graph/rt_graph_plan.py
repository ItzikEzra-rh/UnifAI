from typing import List, Dict, Optional, Iterator, Any, Set
from session.session_registry import SessionRegistry
from core.element_card_builder import ElementCardBuilder
from core.models import ElementCard
from core.enums import ResourceCategory
from blueprints.models.blueprint import BlueprintSpec, ResourceSpec, StepDef
from core.ref.models import NodeRef
from .graph_plan import GraphPlan
from .models import Step, RTStep
from .models import StepContext


class RTGraphPlan:
    """
    Runtime-enabled GraphPlan wrapper.

    Composes a logical GraphPlan and provides the same interface
    but with RTStep objects containing bound callables.
    """

    def __init__(self, logical_plan: GraphPlan, session_registry: SessionRegistry):
        self._logical_plan = logical_plan
        self._session = session_registry
        self._card_builder = ElementCardBuilder(session_registry)
        self._rt_steps: Dict[str, RTStep] = {}
        self._build_runtime_steps()

    @property
    def steps(self) -> List[RTStep]:
        """Get all runtime steps."""
        return list(self._rt_steps.values())

    def get_step(self, uid: str) -> Optional[RTStep]:
        """Get runtime step by uid."""
        return self._rt_steps.get(uid)

    def get_roots(self) -> List[RTStep]:
        """Get steps with no dependencies."""
        return [self._rt_steps[s.uid] for s in self._logical_plan.get_roots()]

    def get_leaves(self) -> List[RTStep]:
        """Get steps with no dependents."""
        return [self._rt_steps[s.uid] for s in self._logical_plan.get_leaves()]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for debugging (delegates to logical plan)."""
        return self._logical_plan.to_dict()

    def add_step(self, step: RTStep) -> None:
        """Add step (for interface compatibility if needed)."""
        raise NotImplementedError("RTGraphPlan is immutable after construction")

    def remove_step(self, uid: str) -> None:
        """Remove step (for interface compatibility if needed)."""
        raise NotImplementedError("RTGraphPlan is immutable after construction")

    def pretty_print(self) -> None:
        """Print plan structure (delegates to logical plan)."""
        self._logical_plan.pretty_print()

    def __iter__(self) -> Iterator[RTStep]:
        """Iterate over runtime steps."""
        return iter(self.steps)

    def __len__(self) -> int:
        """Number of steps."""
        return len(self._rt_steps)

    # ------------------------------------------------------------------ #
    #  Deployment info (for distributed engines like Temporal)
    # ------------------------------------------------------------------ #

    def get_node_blueprint(self, uid: str) -> Dict[str, Any]:
        """
        Return a serialized mini BlueprintSpec for this node.

        Contains ONLY the resources this node needs (its LLM, providers,
        tools, etc.) — not the entire blueprint. Used by distributed
        engines to rebuild a single node on a remote worker.
        """
        step = self._rt_steps.get(uid)
        if step is None:
            raise ValueError(f"Step '{uid}' not found")

        node_elem = self._session.get(ResourceCategory.NODE, step.rid)
        node_spec = node_elem.resource_spec

        # Find dependency rids from the node's config
        # mode="json" preserves $ref: prefix so _collect_refs can find them
        dep_rids = _collect_refs(node_spec.config.model_dump(mode="json"))

        # Gather dependency resource specs by looking up each rid
        llms = []
        providers = []
        tools = []
        retrievers = []
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
            plan=[StepDef(uid=uid, node=NodeRef(node_spec.rid.root))],
            name="mini",
            description="",
        )
        return mini_bp.model_dump(mode="json")

    def get_condition_blueprint(self, condition_rid: str) -> Dict[str, Any]:
        """
        Return a serialized mini BlueprintSpec for a condition.

        Conditions are typically lightweight (no LLM, no tools).
        """
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

    def get_node_context(self, uid: str) -> Dict[str, Any]:
        """
        Return the serialized StepContext for this node.

        Built from the FULL graph topology (adjacent nodes, finalizer
        distances, etc.). Used by distributed engines to inject the
        correct graph awareness into a remotely-built node.
        """
        step = self._rt_steps.get(uid)
        if step is None:
            raise ValueError(f"Step '{uid}' not found")

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

    def _find_resource_spec(self, rid: str):
        """Look up a rid across all resource categories. Returns (category, spec) or None."""
        for category in ResourceCategory:
            try:
                elem = self._session.get(category, rid)
                return category, elem.resource_spec
            except (KeyError, IndexError):
                continue
        return None

    # ------------------------------------------------------------------ #
    #  Private Implementation
    # ------------------------------------------------------------------ #

    def _build_runtime_steps(self) -> None:
        """Build all runtime steps from logical steps."""
        for logical_step in self._logical_plan.steps:
            rt_step = self._create_runtime_step(logical_step)
            self._rt_steps[logical_step.uid] = rt_step

    def _create_runtime_step(self, step: Step) -> RTStep:
        """Create a runtime step from a logical step."""
        # ------------------------------------------------------------------ #
        # 1. Build rich StepContext (adjacent nodes + branching logic + topology)
        # ------------------------------------------------------------------ #
        from .models import AdjacentNodes
        from .topology.finalizer_analyzer import FinalizerAnalyzer
        
        adjacent_nodes_dict = {}
        
        # Find direct connections: steps that have this step in their 'after' list
        for other_step in self._logical_plan.steps:
            if step.uid in other_step.after:
                # This other_step executes directly after current step
                card = self._card_builder.build_card(
                    ResourceCategory.NODE, 
                    other_step.rid,
                    uid=other_step.uid, 
                    metadata=other_step.meta
                )
                adjacent_nodes_dict[other_step.uid] = card
        
        # Add conditional connections (branches from this step)
        branches: Dict[str, str] = step.branches or {}
        for outcome, next_uid in branches.items():
            tgt = self._logical_plan.get_step(next_uid)
            if tgt is not None:
                card = self._card_builder.build_card(
                    ResourceCategory.NODE,
                    tgt.rid,
                    uid=tgt.uid,
                    metadata=tgt.meta
                )
                adjacent_nodes_dict[next_uid] = card

        # Create clean Pydantic model
        adjacent_nodes = AdjacentNodes.from_dict(adjacent_nodes_dict)
        
        # ------------------------------------------------------------------ #
        # 2. Analyze topology (paths to finalizers with cycle prevention)
        # ------------------------------------------------------------------ #
        analyzer = FinalizerAnalyzer(output_channel="output")  # Channel.OUTPUT maps to "output"
        adjacent_node_uids = list(adjacent_nodes_dict.keys())
        
        topology = analyzer.analyze_node_topology(
            plan=self._logical_plan,
            from_node_uid=step.uid,
            adjacent_node_uids=adjacent_node_uids
        )

        step_context = StepContext(
            uid=step.uid,
            metadata=step.meta,
            adjacent_nodes=adjacent_nodes,
            branches=branches,
            topology=topology,
        )

        # ------------------------------------------------------------------ #
        # 3. Bind node & condition callables + inject context
        # ------------------------------------------------------------------ #

        node_func = self._session.get_instance(ResourceCategory.NODE, step.rid)
        if hasattr(node_func, "set_context"):
            node_func.set_context(step_context)

        condition_func = None
        if step.condition:
            condition_func = self._session.get_instance(ResourceCategory.CONDITION, step.condition.rid)
            if hasattr(condition_func, "set_context"):
                condition_func.set_context(step_context)

        return RTStep(
            step=step,
            func=node_func,
            exit_condition=condition_func,
        )


# ------------------------------------------------------------------ #
#  Module-level helpers
# ------------------------------------------------------------------ #

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
