from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import MockAgentNodeConfig
from ..mock_agent_node_factory import MockAgentNodeFactory


class MockAgentNodeElementSpec(BaseElementSpec):
    """Element specification for Mock Agent Node."""

    category = ResourceCategory.NODE
    type_key = "mock_agent_node"
    name = "Mock Agent Node"
    description = "Returns mock responses for testing"
    config_schema = MockAgentNodeConfig
    factory_cls = MockAgentNodeFactory
    tags = ["agent", "node", "mock", "test", "response"]
