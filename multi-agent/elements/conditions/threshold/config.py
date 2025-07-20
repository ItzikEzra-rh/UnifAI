from typing import Literal
from pydantic import Field
from ..common.base_config import BaseConditionConfig
from .identifiers import ELEMENT_TYPE_KEY


class ThresholdConditionConfig(BaseConditionConfig):
    """
    Configuration for a threshold condition:

      - input_key: the key in `state` to compare
      - threshold: numeric cutoff
      - operator: comparison operator
    """
    type: Literal[ELEMENT_TYPE_KEY] = ELEMENT_TYPE_KEY
    input_key: str = Field(
        ..., description="State key to fetch the value"
    )
    threshold: float = Field(
        ..., description="Threshold to compare against"
    )
    operator: Literal[">", "<", ">=", "<=", "==", "!="] = Field(
        ">", description="Comparison operator"
    )
