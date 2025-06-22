from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from tools.models.tool_config import AdditionToolConfig
from tools.addition_tool import AdditionTool


@register_element(
    category=AdditionToolConfig.Meta.category,
    type_key=AdditionToolConfig.Meta.type,
    config_schema=AdditionToolConfig,
    description=AdditionToolConfig.Meta.description
)
class AdditionToolFactory(BaseFactory[AdditionToolConfig, AdditionTool]):
    """
    Factory for creating AdditionTool clients from an AdditionToolConfig.
    """

    def accepts(self, cfg: AdditionToolConfig) -> bool:
        return cfg.type == "add"

    def create(self, cfg: AdditionToolConfig, **kwargs: Any) -> AdditionTool:
        """
        Instantiate an AdditionToolConfig using validated config values.

        :param cfg: Fully‐validated AdditionToolConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = AdditionTool()
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"AdditionToolConfig.create() failed: {e}",
                cfg.dict()
            ) from e
