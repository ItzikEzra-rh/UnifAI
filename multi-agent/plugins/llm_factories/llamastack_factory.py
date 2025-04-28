# plugins/llm_factories/llamastack_factory.py

from typing import Any, Dict
from pydantic import ValidationError
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.llm_config import LLMConfig
from llms.llamastack_llm import LlamaStackLLM


class LlamaStackFactory(BaseFactory):
    """
    Factory for creating LlamaStack-based LLM clients.

    Validates config and instantiates LlamaStackLLM with endpoint and headers.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Recognize configs with 'type': 'llamastack'.
        """
        return cfg.get("type") == "llamastack"

    def create(self, cfg: Dict[str, Any]) -> LlamaStackLLM:
        """
        Validate cfg and create a LlamaStackLLM instance.

        :param cfg: config dict with keys:
            - name (str)
            - type == "llamastack"
            - endpoint (HttpUrl)
            - headers (Dict[str, str], optional)
        :raises PluginConfigurationError: on invalid config or instantiation error
        :return: LlamaStackLLM
        """
        try:
            data = LLMConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("LlamaStack LLM config validation error", cfg) from ve

        try:
            client = LlamaStackLLM(
                endpoint=data.endpoint,
                headers=data.headers or {},
            )
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create LlamaStackLLM: {e}", cfg) from e

        return client
