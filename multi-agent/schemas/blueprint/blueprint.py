from typing import Union, Optional, List, Dict
from pydantic import BaseModel, Field, Extra, field_validator
from schemas.nodes.base_node import NodeSpec
from schemas.llm.base_llm import LLMsSpec
from schemas.retriever.retriever_config import RetrieversSpec
from schemas.condition.base_condition import ConditionSpec
from uuid import uuid4


class StepMeta(BaseModel):
    description: str = Field(default="", description="Short title or label for the step instance")
    display_name: str = Field(default="", description="Custom description for this step's purpose")
    tags: List[str] = Field(default_factory=list, description="Step-defined tags for categorization")


class ToolDef(BaseModel):
    name: str
    type: str


class StepDef(BaseModel):
    uid: str = Field(default_factory=lambda: str(uuid4()))
    after: Optional[Union[str, List[str]]] = None
    exit_condition: Optional[str] = None
    branches: Optional[dict] = None
    node: NodeSpec
    meta: Optional[StepMeta] = Field(
        default_factory=lambda: StepMeta(),
        description="Step-defined metadata for this step instance"
    )

    @field_validator("meta", mode="before")
    @classmethod
    def ensure_default_meta(cls, v):
        return StepMeta() if v is None else v


class BlueprintSpec(BaseModel):
    llms: List[LLMsSpec] = Field(default_factory=list)
    retrievers: List[RetrieversSpec] = Field(default_factory=list)
    conditions: List[ConditionSpec] = Field(default_factory=list)
    tools: List[ToolDef] = Field(default_factory=list)
    plan: List[StepDef]
    description: Optional[str] = "Blueprint description"
    display_name: Optional[str] = "Display Name"
    display_description: Optional[str] = "Display description"

    class Config:
        extra = Extra.forbid
