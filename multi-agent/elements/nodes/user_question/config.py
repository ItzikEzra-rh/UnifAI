from typing import Literal
from .identifiers import ELEMENT_TYPE_KEY
from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field


class UserQuestionNodeConfig(NodeBaseConfig):
    """
    Logs or passes through user input without modification.
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
