# graph/blueprint_loader.py

import yaml
from typing import Union
from schemas.blueprint_schema import Blueprint
from core.graph_context import GraphContext
from composers.plan_composer import PlanComposer


class BlueprintLoader:
    """
    Loads a YAML or dict-based Blueprint, composes a GraphPlan via PlanComposer,
    and compiles it in a given GraphContext with the specified builder.
    """

    @staticmethod
    def load_from_file(
            path: str,
            context: GraphContext,
            builder: Any
    ) -> None:
        """
        Parse YAML at `path`, build and compile the graph in `context`.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        BlueprintLoader.load_from_dict(data, context, builder)

    @staticmethod
    def load_from_dict(
            data: Dict,
            context: GraphContext,
            builder: Any
    ) -> None:
        """
        Given a raw dict (e.g. from JSON or UI), validate it as Blueprint,
        then use PlanComposer to assemble and compile into context.
        """
        blueprint = Blueprint.parse_obj(data)

        # 1) Pre-load dynamic components
        for llm_cfg in blueprint.llms:
            context.plugin_registry.get_llm(llm_cfg.dict())
        for tool_cfg in blueprint.tools:
            context.plugin_registry.get_tool(tool_cfg.dict())
        for ret_cfg in blueprint.retrievers:
            context.plugin_registry.get_retriever(ret_cfg.dict())
        for agent_cfg in blueprint.agents:
            context.plugin_registry.get_agent(agent_cfg.dict())

        # 2) Build Plan
        composer = PlanComposer(context)
        for step in blueprint.plan:
            composer.add_step(step)

        # 3) Compile into executable graph
        composer.finalize(builder)
