from elements.common.base_factory import BaseFactory
from elements.common.exceptions import PluginConfigurationError
from .config import ThresholdConditionConfig
from .threshold import ThresholdCondition
from .identifiers import ELEMENT_TYPE_KEY


class ThresholdConditionFactory(BaseFactory[ThresholdConditionConfig, ThresholdCondition]):
    """
    Factory that builds a ThresholdCondition from its config.
    """

    def accepts(self, cfg: ThresholdConditionConfig, element_type: str) -> bool:
        return element_type == ELEMENT_TYPE_KEY

    def create(self, cfg: ThresholdConditionConfig, **deps) -> ThresholdCondition:
        try:
            return ThresholdCondition(
                input_key=cfg.input_key,
                threshold=cfg.threshold,
                operator=cfg.operator
            )
        except Exception as e:
            raise PluginConfigurationError(
                f"ThresholdConditionFactory.create failed: {e}",
                cfg.dict()
            ) from e
