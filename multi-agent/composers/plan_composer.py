# composers/plan_composer.py

from typing import Union, List
from pydantic import BaseModel
from graph.graph_plan import GraphPlan, Step
from schemas.blueprint_schema import StepSpec
from schemas.node_config import NodeSpec
from core.graph_context import GraphContext
from composers.agent_composer import AgentComposer
from composers.tool_wrapper_composer import ToolNodeComposer


class PlanComposer:
    """
    Builds a GraphPlan from a list of StepSpec objects.

    - Delegates agent/node creation to AgentComposer.
    - Delegates single-tool wrapping to ToolNodeComposer.
    - Uses ComponentRegistry for static node lookups.
    """

    def __init__(self, context: GraphContext):
        self.ctx = context
        self.plan = GraphPlan()

    def add_step(self, step_spec: StepSpec) -> None:
        """
        Add a single step to the internal GraphPlan.

        :param step_spec: validated StepSpec from blueprint_schema.
        """
        name = step_spec.name
        after = step_spec.after

        # Determine the node factory function
        node_field = step_spec.node
        if isinstance(node_field, str):
            # Static, pre-registered node
            func = self.ctx.base_registry.get_node(node_field)

        else:
            # Dynamic NodeSpec
            spec: NodeSpec = node_field
            spec.validate_mode()

            # Branch by inline-type vs. template-ref
            if spec.ref:
                # Merge template + overrides, then treat as inline
                template = self.ctx.base_registry.get_node(spec.ref)
                merged = template.dict()
                overrides = spec.dict(exclude_unset=True, exclude={"ref"})
                merged.update(overrides)
                func = self._build_from_spec(merged)

            else:
                # Pure inline definition
                func = self._build_from_spec(spec.dict())

        # Register the step
        self.plan.add_step(name=name, func=func, after=after)

    def _build_from_spec(self, cfg: dict):
        """
        Dispatch to the appropriate composer by `type` field.
        """
        node_type = cfg.get("type")
        if node_type == "custom_agent":
            return AgentComposer.build(cfg, self.ctx.plugin_registry)
        if node_type == "tool_node":
            return ToolNodeComposer.build(cfg, self.ctx.plugin_registry)
        if node_type == "discussion":
            # Future: DiscussionNodeComposer.build(...)
            return self.ctx.base_registry.get_node("discussion")(self.ctx.plugin_registry.get_llm(cfg["llm"]))
        if node_type == "critic":
            return self.ctx.base_registry.get_node("critic")(self.ctx.plugin_registry.get_llm(cfg["llm"]))
        raise ValueError(f"Unsupported node type: {node_type}")

    def finalize(self, builder) -> None:
        """
        Compile the accumulated GraphPlan into an executable graph
        within the GraphContext.
        """
        self.ctx.compile_plan(self.plan, builder)
