from pydantic import BaseModel, Field, Extra


class BaseConditionConfig(BaseModel):
    """
    Common fields for all conditions.
    Pure configuration schema - no UI metadata.
    
    Concrete condition schemas must subclass this and set a
    literal `type` field for discrimination.
    UI metadata is now handled by ElementSpec classes.
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


