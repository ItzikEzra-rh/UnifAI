from elements.common.base_element_spec import BaseElementSpec
from ..threshold_factory import ThresholdConditionFactory
from core.enums import ResourceCategory
from ..config import ThresholdConditionConfig
from ..identifiers import ELEMENT_TYPE_KEY


class ThresholdConditionElementSpec(BaseElementSpec):
    """Element specification for Threshold Condition."""

    category = ResourceCategory.CONDITION
    name = "Threshold Condition"
    type_key = ELEMENT_TYPE_KEY
    description = "Triggers when the state's value crosses the numeric threshold"
    config_schema = ThresholdConditionConfig
    factory_cls = ThresholdConditionFactory
    tags = ["condition", "threshold", "numeric"]
