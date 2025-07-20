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

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
