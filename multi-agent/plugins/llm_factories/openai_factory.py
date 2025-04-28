# plugins/llm_factories/openai_factory.py

from typing import Any, Dict
from pydantic import ValidationError
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.llm.openai_config import OpenAIConfig
from llms.openai_llm import OpenAILLM
from plugins.decorators import register_element


@register_element(
    name="openai_llm",
    element_type="llm",
    description="OpenAI official API",
    config_schema=OpenAIConfig,
)
class OpenAIFactory(BaseFactory):
    """
    Factory for creating OpenAI-based LLM clients.

    Validates incoming config with LLMConfig, then instantiates OpenAILLM.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Return True if cfg indicates an OpenAI LLM.

        :param cfg: configuration dict, must contain 'type': 'openai'
        """
        return cfg.get("type") == "openai"

    def create(self, cfg: Dict[str, Any]) -> OpenAILLM:
        """
        Validate cfg and create an OpenAILLM instance.

        :param cfg: config dict with keys:
            - name (str)
            - type == "openai"
            - base_url (HttpUrl)
            - api_key (str)
            - model (str)
            - temperature (float, optional)
        :raises PluginConfigurationError: on missing/invalid fields
        :return: OpenAILLM
        """
        try:
            # Validate and coerce types
            data = LLMConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("OpenAI LLM config validation error", cfg) from ve

        # Instantiate the OpenAI wrapper
        try:
            client = OpenAILLM(
                base_url=data.base_url,
                api_key=data.api_key,
                model=data.model,
                temperature=data.temperature,
            )
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create OpenAILLM: {e}", cfg) from e

        return client
