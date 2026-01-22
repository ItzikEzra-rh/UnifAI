from typing import Any
from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import OcExecToolConfig
from .oc_exec import OcExecTool
from .identifiers import Identifier


class OcExecToolFactory(BaseFactory[OcExecToolConfig, OcExecTool]):
    """
    Factory for creating OcExecTool clients from an OcExecToolConfig.
    """

    def accepts(self, cfg: OcExecToolConfig, element_type: str) -> bool:
        return element_type == Identifier.TYPE

    def create(self, cfg: OcExecToolConfig, **kwargs: Any) -> OcExecTool:
        """
        Instantiate an OcExecTool using validated config values.

        :param cfg: Fully-validated OcExecToolConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = OcExecTool(
                server=cfg.server,
                token=cfg.token,
                namespace=cfg.namespace,
                insecure_skip_tls_verify=cfg.insecure_skip_tls_verify,
            )
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"OcExecToolFactory.create() failed: {e}",
                cfg.dict()
            ) from e
