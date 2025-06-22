from dataclasses import dataclass
from typing import Optional, Type
from pydantic import BaseModel
from plugins.base_factory import BaseFactory
from core.enums import ResourceCategory


@dataclass(frozen=True)
class ElementDefinition:
    """
    Holds all the metadata for one plugin element.
    """
    category: ResourceCategory  # e.g. "llm", "tool", "node"
    type_key: str  # e.g. "openai", "calculator", "custom_agent_node"
    factory_cls: Type[BaseFactory]  # the factory class to call .create()
    schema_cls: Optional[Type[BaseModel]] = None  # pydantic schema for validation
    description: str = ""  # human‐readable summary
