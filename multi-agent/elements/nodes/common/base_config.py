from typing import Optional, List, Union, Annotated
from pydantic import BaseModel, Field, Extra
from core.ref.models import Ref


class NodeBaseConfig(BaseModel):
    """
    Common fields for all node types.
    Pure configuration schema - no UI metadata.
    
    Defines all atomic node fields as optional by default.
    Subclasses will override required ones as needed.
    UI metadata is now handled by ElementSpec classes.
    """
    name: Optional[str] = Field(None, description="Optional node instance name")
    llm: Optional[Ref] = Field(None, description="LLM key to use")
    retriever: Optional[Ref] = Field(None, description="Retriever key to use")
    tools: List[Ref] = Field(default_factory=list, description="List of tool keys")
    system_message: Optional[str] = Field(None, description="Custom system prompt")
    retries: Optional[int] = Field(1, description="Retry count if failure")

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True


