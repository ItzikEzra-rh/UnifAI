from registry.element_registry import ElementRegistry
from registry.element_definition import ElementDefinition
from typing import Optional, Type
from pydantic import BaseModel
from plugins.base_factory import BaseFactory


def register_element(
        *,
        category: str,
        type_key: str,
        description: str = "",
        config_schema: Optional[Type[BaseModel]] = None
):
    def decorator(factory_cls: Type[BaseFactory]):
        edef = ElementDefinition(
            category=category,
            type_key=type_key,
            factory_cls=factory_cls,
            schema_cls=config_schema,
            description=description
        )
        ElementRegistry().register_element(edef)
        return factory_cls

    return decorator
