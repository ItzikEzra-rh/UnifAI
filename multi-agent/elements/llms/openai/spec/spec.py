from elements.common.base_element_spec import BaseElementSpec
from ..openai_factory import OpenAIFactory
from core.enums import ResourceCategory
from ..config import OpenAIConfig
from ..identifiers import ELEMENT_TYPE_KEY


class OpenAIElementSpec(BaseElementSpec):
    """
    Element specification for OpenAI LLM.
    
    Provides all metadata needed for UI integration and runtime configuration.
    """
    category = ResourceCategory.LLM
    type_key = ELEMENT_TYPE_KEY
    name = "OpenAI LLM"
    description = "Official OpenAI API configuration for LLM interactions"
    config_schema = OpenAIConfig
    factory_cls = OpenAIFactory
    tags = ["llm", "openai", "api", "chat"]
