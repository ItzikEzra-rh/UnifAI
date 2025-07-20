from typing import ClassVar
from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import FinalAnswerNodeConfig
from ..final_answer_node_factory import FinalAnswerNodeFactory
from ..identifiers import ELEMENT_TYPE_KEY


class FinalAnswerNodeElementSpec(BaseElementSpec):
    """Element specification for Final Answer Node."""

    category: ClassVar[ResourceCategory] = ResourceCategory.NODE
    type_key = ELEMENT_TYPE_KEY
    name = "Final Answer Node"
    description = "Outputs the final response"
    config_schema = FinalAnswerNodeConfig
    factory_cls = FinalAnswerNodeFactory
    tags = ["node", "final", "answer", "response", "output"]
