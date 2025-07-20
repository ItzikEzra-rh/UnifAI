from typing import Literal
from elements.nodes.common.base_config import NodeBaseConfig


class FinalAnswerNodeConfig(NodeBaseConfig):
    """
    Emits the final aggregated answer without overrides.
    """
    type: Literal["final_answer_node"] = "final_answer_node"
