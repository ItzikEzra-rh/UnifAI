from typing import Literal
from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field


class UserQuestionNodeConfig(NodeBaseConfig):
    """
    Logs or passes through user input without modification.
    """
    name: str = Field(None, description="Optional node instance name")
