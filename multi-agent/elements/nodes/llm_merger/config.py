from typing import Literal
from elements.nodes.common.base_config import NodeBaseConfig


class MergerLLMNodeConfig(NodeBaseConfig):
    """
    Node that merges outputs from multiple agents.
    """
    type: Literal["merger_node"] = "merger_node" 