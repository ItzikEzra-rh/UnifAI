from typing import Union, Optional, List, Dict
from pydantic import BaseModel, Field
from schemas.nodes.base_node import NodeSpec
from schemas.llm.base_llm import LLMsSpec
from schemas.condition.base_condition import ConditionSpec


class RetrieverDef(BaseModel):
    name: str
    type: str


class ToolDef(BaseModel):
    name: str
    type: str


class StepDef(BaseModel):
    name: str
    after: Optional[Union[str, List[str]]] = None
    exit_condition: Optional[str] = None
    branches: Optional[dict] = None
    node: NodeSpec


class BlueprintSpec(BaseModel):
    llms: List[LLMsSpec] = Field(default_factory=list)
    retrievers: List[RetrieverDef] = Field(default_factory=list)
    conditions: List[ConditionSpec] = Field(default_factory=list)
    tools: List[ToolDef] = Field(default_factory=list)
    plan: List[StepDef]
