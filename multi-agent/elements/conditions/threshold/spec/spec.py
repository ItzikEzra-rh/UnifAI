from elements.common.base_element_spec import BaseElementSpec
from ..threshold_factory import ThresholdConditionFactory
from core.enums import ResourceCategory
from ..config import ThresholdConditionConfig


class ThresholdConditionElementSpec(BaseElementSpec):
    """Element specification for Threshold Condition."""

    category = ResourceCategory.CONDITION
    name = "Threshold Condition"
    type_key = "threshold"
    description = "Triggers when the state's value crosses the numeric threshold"
    config_schema = ThresholdConditionConfig
    factory_cls = ThresholdConditionFactory
    tags = ["condition", "threshold", "numeric"]
