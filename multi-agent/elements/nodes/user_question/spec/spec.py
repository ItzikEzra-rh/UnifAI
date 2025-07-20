from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import UserQuestionNodeConfig
from ..user_question_node_factory import UserQuestionNodeFactory
from ..identifiers import ELEMENT_TYPE_KEY


class UserQuestionNodeElementSpec(BaseElementSpec):
    """Element specification for User Question Node."""

    category = ResourceCategory.NODE
    type_key = ELEMENT_TYPE_KEY
    name = "User Question Node"
    description = "Captures and forwards the user's question"
    config_schema = UserQuestionNodeConfig
    factory_cls = UserQuestionNodeFactory
    tags = ["node", "user", "question", "input", "capture"]
