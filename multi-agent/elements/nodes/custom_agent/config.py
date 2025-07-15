from typing import Literal
from elements.nodes.common.base_config import NodeBaseConfig


class CustomAgentNodeConfig(NodeBaseConfig):
    """
    Custom agent node with full override capabilities.
    """
    type: Literal["custom_agent_node"] = "custom_agent_node"
