from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.tools.tool_config import DivisionToolConfig
from tools.division_tool import DivisionTool


@register_element(
    category=DivisionToolConfig.Meta.category,
    type_key=DivisionToolConfig.Meta.type,
    config_schema=DivisionToolConfig,
    description=DivisionToolConfig.Meta.description
)
class DivisionToolFactory(BaseFactory[DivisionToolConfig, DivisionTool]):
    """
    Factory for creating Division clients from an DivisionToolConfig.
    """

    def accepts(self, cfg: DivisionToolConfig) -> bool:
        return cfg.type == "divide"

    def create(self, cfg: DivisionToolConfig, **kwargs: Any) -> DivisionTool:
        """
        Instantiate an DivisionToolConfig using validated config values.

        :param cfg: Fully‐validated DivisionToolConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = DivisionTool()
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"DivisionToolConfig.create() failed: {e}",
                cfg.dict()
            ) from e
