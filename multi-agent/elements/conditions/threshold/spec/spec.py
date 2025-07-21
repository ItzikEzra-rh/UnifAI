from elements.common.base_element_spec import BaseElementSpec
from ..threshold_factory import ThresholdConditionFactory
from core.enums import ResourceCategory
from ..config import ThresholdConditionConfig
from ..identifiers import Identifier, META


class ThresholdConditionElementSpec(BaseElementSpec):
    """Element specification for Threshold Condition."""

    category = ResourceCategory.CONDITION
    type_key = Identifier.TYPE
    name = META.name
    description = META.description
    config_schema = ThresholdConditionConfig
    factory_cls = ThresholdConditionFactory
    tags = META.tags
