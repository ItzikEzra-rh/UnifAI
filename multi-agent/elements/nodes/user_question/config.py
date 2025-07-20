from typing import Literal
from elements.nodes.common.base_config import NodeBaseConfig
from pydantic import Field


class UserQuestionNodeConfig(NodeBaseConfig):
    """
    Logs or passes through user input without modification.
    """
    type: Literal["user_question_node"] = "user_question_node"
