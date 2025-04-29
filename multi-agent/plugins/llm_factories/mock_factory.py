# plugins/llm_factories/mock_factory.py

from typing import Any, Dict
from pydantic import ValidationError
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from schemas.llm.mock_config import MockLLMConfig, LLMConfig
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

    def accepts(self, cfg: MockLLMConfig) -> bool:
        """
        Recognize configs with 'type': 'mock'.
        """
        return cfg.type == "mock"

    def create(self, cfg: MockLLMConfig) -> MockLLM:
        """
        Validate cfg and return a MockLLM.

        :param cfg: config dict with keys:
            - name (str)
            - type == "mock"
        :raises PluginConfigurationError: on validation failure
        """
        try:
            return MockLLM()
        except Exception as e:
            raise PluginConfigurationError(f"Failed to create MockLLM: {e}", cfg) from e
