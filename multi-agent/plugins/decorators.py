# plugins/decorators.py

from registry.element_registry import element_registry


def register_element(name: str, element_type: str, description: str = "", config_schema: type = None):
    """
    Decorator for factories or static nodes to register them into the global ElementRegistry.

    Args:
        name (str): Unique name for this element (e.g., "openai_llm", "slack_agent").
        element_type (str): Category ("llm", "tool", "agent", "node").
        description (str): Optional human-readable description.
        config_schema (type): Optional Pydantic BaseModel config schema.
    """

    def decorator(cls):
        element_registry.register(
            name=name,
            element_type=element_type,
            description=description,
            config_schema=config_schema,
            cls=cls,
        )
        return cls

    return decorator
