# composers/tool_wrapper_composer.py

from typing import Dict, Any
from schemas.node_config import NodeSpec
from nodes.tool_node import ToolNode
from plugins.exceptions import PluginConfigurationError


class ToolNodeComposer:
    """
    Wraps a single tool invocation into a Node callable.

    Expects cfg dict to contain:
      - name: step name (optional here; will be assigned by PlanComposer)
      - type: "tool_node"
      - tool: name or cfg of the tool
      - input_map: mapping from state keys → tool args
    """

    @staticmethod
    def build(cfg: Dict[str, Any], registry: PluginRegistry) -> ToolNode:
        # Validate minimal required fields
        try:
            spec = NodeSpec(**cfg)
            if spec.type != "tool_node":
                raise ValueError("ToolNodeComposer only handles type='tool_node'")
            if not spec.tool or not spec.input_map:
                raise ValueError("ToolNodeComposer requires 'tool' and 'input_map'")
        except Exception as e:
            raise PluginConfigurationError("Invalid tool_node spec", cfg) from e

        # Resolve the tool instance
        try:
            tool = registry.get_tool(spec.tool)
        except Exception as e:
            raise PluginConfigurationError("Failed to resolve tool for ToolNode", cfg) from e

        # Instantiate and return the node
        try:
            return ToolNode(tool=tool, input_map=spec.input_map)
        except Exception as e:
            raise PluginConfigurationError("Failed to instantiate ToolNode", cfg) from e
