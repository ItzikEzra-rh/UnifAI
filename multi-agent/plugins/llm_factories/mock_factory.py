# plugins/llm_factories/mock_factory.py

from typing import Any, Dict
from pydantic import ValidationError
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.llm.mock_config import MockLLMConfig
from llms.mock_llm import MockLLM
from plugins.decorators import register_element


@register_element(
    name="mock_llm",
    element_type="llm",
    description="Mock API",
    config_schema=MockLLMConfig,
)
class MockLLMFactory(BaseFactory):
    """
    Factory for creating a MockLLM instance for testing.

    Ensures config is well-formed (type="mock") but otherwise returns a stateless mock.
    """

    def accepts(self, cfg: Dict[str, Any]) -> bool:
        """
        Recognize configs with 'type': 'mock'.
        """
        return cfg.get("type") == "mock"

    def create(self, cfg: Dict[str, Any]) -> MockLLM:
        """
        Validate cfg and return a MockLLM.

        :param cfg: config dict with keys:
            - name (str)
            - type == "mock"
        :raises PluginConfigurationError: on validation failure
        """
        try:
            # We still run through LLMConfig to ensure 'name' etc. are present
            LLMConfig(**cfg)
        except ValidationError as ve:
            raise PluginConfigurationError("MockLLM config validation error", cfg) from ve

        try:
            return MockLLM()
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create MockLLM: {e}", cfg) from e
