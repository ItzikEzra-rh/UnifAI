from typing import ClassVar, Literal, Union, Annotated, Protocol
from pydantic import BaseModel, Field, Extra, SkipValidation
from core.enums import ResourceCategory


# Protocol for condition metadata
class ConditionMeta(Protocol):
    category: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]


# Base condition config with shared fields and default Meta
class BaseConditionConfig(BaseModel):
    """
    Shared fields for all conditions.
    Concrete condition schemas must subclass this and set a
    literal `type` field for discrimination.
    """
    name: str = Field(
        None, description="Optional identifier for this condition"
    )
    type: str = Field(
        ..., description="Discriminator: which condition to evaluate"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(ConditionMeta):
        category: ClassVar[SkipValidation[str]] = ResourceCategory.CONDITION
        display_name: ClassVar[SkipValidation[str]] = "Base Condition"
        description: ClassVar[SkipValidation[str]] = "Abstract base for all condition configs"
        type: ClassVar[SkipValidation[str]] = "base"


# Threshold condition config with specific metadata
class ThresholdConditionConfig(BaseConditionConfig):
    """
    Configuration for a threshold condition:

      - input_key: the key in `state` to compare
      - threshold: numeric cutoff
      - operator: comparison operator
    """
    type: Literal["threshold"] = "threshold"
    input_key: str = Field(
        ..., description="State key to fetch the value"
    )
    threshold: float = Field(
        ..., description="Threshold to compare against"
    )
    operator: Literal[">", "<", ">=", "<=", "==", "!="] = Field(
        ">", description="Comparison operator"
    )

    class Meta(BaseConditionConfig.Meta):
        display_name: ClassVar[SkipValidation[str]] = "Threshold Condition"
        description: ClassVar[SkipValidation[str]] = (
            "Triggers when the state's value crosses the numeric threshold"
        )
        type: ClassVar[SkipValidation[str]] = "threshold"


# Discriminated union for condition specifications
ConditionSpec = Annotated[
    Union[
        ThresholdConditionConfig,
    ],
    Field(discriminator="type")
]
