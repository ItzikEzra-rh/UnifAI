from typing import List
from blueprints.models.blueprint import StepDef
from graph.graph_plan import GraphPlan
from graph.step_context import StepContext
from core.enums import ResourceCategory
from core.contracts import SessionRegistry


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
            func = self.session.get(ResourceCategory.NODE, sd.node.ref)

            # inject context if supported
            if hasattr(func, 'set_context') and callable(func.set_context):
                func.set_context(step_ctx)

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
