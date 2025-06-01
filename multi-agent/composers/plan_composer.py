from typing import List, Union
from session.session_registry import SessionRegistry
from schemas.blueprint.blueprint import StepDef, NodeSpec
from graph.graph_plan import GraphPlan
from .node_factory import NodeFactory
from graph.step_context import StepContext
from core.enums import ResourceCategory


class PlanComposer:
    """
    Converts a list of StepDef objects (from BlueprintSpec.plan)
    into a fully-populated GraphPlan of Step(uid, func, ...).

    - Resolves static nodes by uid via ElementRegistry → NodeConfig templates.
    - Builds dynamic nodes (NodeSpec) via NodeFactory + SessionRegistry.
    - Enforces SOLID separation: only composes plan structure.
    """

    def __init__(
            self,
            session_registry: SessionRegistry,
    ) -> None:
        self.session = session_registry

    def compose(self, step_defs: List[StepDef]) -> GraphPlan:
        plan = GraphPlan()

        for sd in step_defs:
            # normalize 'after' to list
            after = []
            if sd.after:
                if isinstance(sd.after, str):
                    after = [sd.after]
                else:
                    after = sd.after

            # make the step context
            step_ctx = StepContext(uid=sd.uid, metadata=sd.meta)

            # get the condition callable
            cond_fn = self.session.get(ResourceCategory.CONDITION, sd.exit_condition) if sd.exit_condition else None

            # instantiate the node
            func = self._resolve_node(sd.node, step_ctx)

            # 3) add into plan
            plan.add_step(
                uid=sd.uid,
                func=func,
                after=after,
                exit_condition=cond_fn,
                branches=sd.branches,
                metadata=sd.meta,
            )

        # 4) sanity-check references
        plan.validate()
        return plan

    def _resolve_node(self, node_field: Union[str, NodeSpec], step_ctx: StepContext):
        """
        Returns a callable node instance for the plan.

        If node_field is a string → static node:
          • fetch config_schema & Node class from ElementRegistry
          • build a NodeSpec → pass to NodeFactory

        If node_field is a NodeSpec → inline:
          • pass directly to NodeFactory

        NodeFactory merges template defaults + overrides + session atoms.
        """
        if isinstance(node_field, str):
            # static node: name=type
            spec = NodeSpec(type=node_field, name=node_field)
        else:
            spec = node_field

        # Build a BaseNode subclass instance
        node_instance = NodeFactory.build(spec, self.session, step_ctx)

        # Return the callable (we assume BaseNode.__call__ invokes run())
        return node_instance
