from typing import Any
from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.llm.base_llm import OpenAIConfig
from llms.openai_llm import OpenAILLM


@register_element(
    category="llm",
    type_key=OpenAIConfig.model_fields["type"].default,
    config_schema=OpenAIConfig,
    description="OpenAI LLM"
)
class OpenAIFactory(BaseFactory[OpenAIConfig, OpenAILLM]):
    """
    Factory for creating OpenAILLM clients from an OpenAIConfig.
    """

    def accepts(self, cfg: OpenAIConfig) -> bool:
        return cfg.type == "openai"

    def create(self, cfg: OpenAIConfig, **kwargs: Any) -> OpenAILLM:
        """
        Instantiate an OpenAILLM using validated config values.

        :param cfg: Fully‐validated OpenAIConfig
        :raises PluginConfigurationError: if instantiation fails
        """
        try:
            client = OpenAILLM(
                api_key=cfg.api_key,
                api_base=str(cfg.api_base),
                model_name=cfg.model_name,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                azure_deployment_id=cfg.azure_deployment_id,
                timeout=cfg.timeout,
                **cfg.extra
            )
            return client
        except Exception as e:
            raise PluginConfigurationError(
                f"OpenAIFactory.create() failed: {e}",
                cfg.dict()
            ) from e
