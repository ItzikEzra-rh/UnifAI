from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.tools.tool_config import SshExecToolConfig
from tools.ssh_exec import SshExecTool


@register_element(
    category=SshExecToolConfig.Meta.category,
    type_key=SshExecToolConfig.Meta.type,
    config_schema=SshExecToolConfig,
    description=SshExecToolConfig.Meta.description
)
class SshExecToolFactory(BaseFactory[SshExecToolConfig, SshExecTool]):
    """
    Factory for creating SshExecTool clients from an SshExecToolConfig.
    """

    def accepts(self, cfg: SshExecToolConfig) -> bool:
        return cfg.type == "ssh_exec"

    def create(self, cfg: SshExecToolConfig, **kwargs: Any) -> SshExecTool:
        """
        Instantiate an DivisionToolConfig using validated config values.

        :param cfg: Fully‐validated DivisionToolConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = SshExecTool(host=cfg.host,
                                 port=cfg.port,
                                 username=cfg.username,
                                 password=cfg.password)
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"SshExecToolFactory.create() failed: {e}",
                cfg.dict()
            ) from e
