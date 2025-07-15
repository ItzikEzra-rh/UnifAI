from typing import Union, Annotated
from pydantic import Field
from .threshold.config import ThresholdConditionConfig

ConditionSpec = Annotated[
    Union[
        ThresholdConditionConfig,
    ],
    Field(discriminator="type")
]
