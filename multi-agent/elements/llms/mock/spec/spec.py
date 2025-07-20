from elements.common.base_element_spec import BaseElementSpec
from ..mock_factory import MockLLMFactory
from core.enums import ResourceCategory
from ..config import MockLLMConfig
from ..identifiers import ELEMENT_TYPE_KEY


class MockLLMElementSpec(BaseElementSpec):
    """Element specification for Mock LLM - testing and development."""

    category = ResourceCategory.LLM
    type_key = ELEMENT_TYPE_KEY
    name = "Mock LLM"
    description = "Returns a constant or echo—for testing"
    config_schema = MockLLMConfig
    factory_cls = MockLLMFactory  # Factory not defined for mock LLM
    tags = ["llm", "mock", "test", "echo"]
