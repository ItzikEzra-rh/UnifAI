# multi_agent/runtime/runtime_builder.py

from registry.user_registry import UserRegistry
from graph.graph_plan import GraphPlan
from graph.step import Step
from typing import Dict, Any

class RuntimeBuilder:
    """
    Builds a per-user session runtime from a blueprint dictionary:
    - Creates UserRegistry with LLMs, Tools, Agents, Nodes
    - Composes GraphPlan
    """

    def __init__(self):
        pass  # stateless class, just utils

    def build(self, blueprint: Dict[str, Any]) -> tuple[UserRegistry, GraphPlan]:
        """
        Main method to build full runtime from blueprint.

        Args:
            blueprint: Parsed dictionary loaded from YAML or JSON.

        Returns:
            (UserRegistry, GraphPlan)
        """

        registry = UserRegistry()
        plan = GraphPlan()

        # --- Instantiate LLMs ---
        for llm_def in blueprint.get("llms", []):
            name = llm_def["name"]
            config_overrides = llm_def.get("config_overrides", {})
            registry.instantiate(name=name, config_overrides=config_overrides)

        # --- Instantiate Tools ---
        for tool_def in blueprint.get("tools", []):
            name = tool_def["name"]
            config_overrides = tool_def.get("config_overrides", {})
            registry.instantiate(name=name, config_overrides=config_overrides)

        # --- Instantiate Agents ---
        for agent_def in blueprint.get("agents", []):
            name = agent_def["name"]
            config_overrides = agent_def.get("config_overrides", {})
            registry.instantiate(name=name, config_overrides=config_overrides)

        # --- Instantiate Nodes ---
        for node_def in blueprint.get("nodes", []):
            name = node_def["name"]
            config_overrides = node_def.get("config_overrides", {})
            registry.instantiate(name=name, config_overrides=config_overrides)

        # --- Compose Plan ---
        for step_def in blueprint.get("plan", []):
            step_name = step_def["name"]
            node_name = step_def["node"]
            after = step_def.get("after")

            if not registry.has_node(node_name):
                raise ValueError(f"Node '{node_name}' referenced in plan but not instantiated.")

            node_instance = registry.get_node(node_name)

            plan.add_step(
                name=step_name,
                func=node_instance,
                after=after,
            )

        return registry, plan
