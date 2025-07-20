from typing import Union, Annotated
from pydantic import Field
from .threshold.config import ThresholdConditionConfig

ConditionSpec = Union[
    ThresholdConditionConfig,
]
