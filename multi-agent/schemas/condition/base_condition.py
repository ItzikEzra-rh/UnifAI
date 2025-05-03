from pydantic import BaseModel, Field, Extra
from typing import Literal, Union, Annotated


class BaseConditionConfig(BaseModel):
    """
    Shared fields for all conditions.
    Concrete condition schemas must subclass this and set a
    literal `type` field for discrimination.
    """
    name: str = Field(None, description="Optional identifier for this condition")
    type: str  # discriminator; e.g. "threshold"

    class Config:
        extra = Extra.forbid


class ThresholdConditionConfig(BaseConditionConfig):
    """
    Configuration for a threshold condition:

      - input_key: the key in `state` to compare
      - threshold: numeric cutoff
      - operator: comparison operator
    """
    type: Literal["threshold"] = "threshold"
    input_key: str = Field(..., description="State key to fetch the value")
    threshold: float = Field(..., description="Threshold to compare against")
    operator: Literal[">", "<", ">=", "<=", "==", "!="] = Field(
        ">", description="Comparison operator"
    )


ConditionSpec = Annotated[
    Union[
        ThresholdConditionConfig,
    ],
    Field(discriminator="type")
]
