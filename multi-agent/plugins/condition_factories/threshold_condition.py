from plugins.decorators import register_element
from plugins.base_factory import BaseFactory
from plugins.exceptions import PluginConfigurationError
from condition.models.base_condition import ThresholdConditionConfig
from condition.threshold_condition import ThresholdCondition


@register_element(
    type_key=ThresholdConditionConfig.Meta.type,
    category=ThresholdConditionConfig.Meta.category,
    config_schema=ThresholdConditionConfig,
    description=ThresholdConditionConfig.Meta.description,
)
class ThresholdConditionFactory(BaseFactory[ThresholdConditionConfig, ThresholdCondition]):
    """
    Factory that builds a ThresholdCondition from its config.
    """

    def accepts(self, cfg: ThresholdConditionConfig) -> bool:
        return cfg.type == "threshold"

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
