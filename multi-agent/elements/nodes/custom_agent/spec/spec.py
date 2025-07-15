from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import CustomAgentNodeConfig
from ..custom_agent_node_factory import CustomAgentNodeFactory


class CustomAgentNodeElementSpec(BaseElementSpec):
    """Element specification for Custom Agent Node."""

    category = ResourceCategory.NODE
    type_key = "custom_agent_node"
    name = "Custom Agent Node"
    description = "Agent node with LLM, retriever, tools, and prompt overrides"
    config_schema = CustomAgentNodeConfig
    factory_cls = CustomAgentNodeFactory
    tags = ["agent", "node", "custom", "llm", "retriever", "tools"]
