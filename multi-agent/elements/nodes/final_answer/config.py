from typing import Literal
from .identifiers import ELEMENT_TYPE_KEY
from elements.nodes.common.base_config import NodeBaseConfig


class FinalAnswerNodeConfig(NodeBaseConfig):
    """
    Emits the final aggregated answer without overrides.
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
