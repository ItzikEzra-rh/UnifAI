from typing import Union, Optional, List, Dict
from pydantic import BaseModel, Field


class LLMDef(BaseModel):
    name: str
    type: str

    # any llm-specific overrides go here


class RetrieverDef(BaseModel):
    name: str
    type: str


class ToolDef(BaseModel):
    name: str
    type: str


class AgentDef(BaseModel):
    name: str
    type: str
    llm: str
    retriever: Optional[str] = None
    tools: Optional[List[str]] = []
    system_message: str
    retries: int = 1


class NodeSpec(BaseModel):
    """
    Inline node definition schema.
    You can add whatever fields you need here (type, agent, llm, retriever, etc).
    """
    name: Optional[str] = None
    type: str
    agent: Optional[str] = None
    llm: Optional[str] = None
    retriever: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    system_message: Optional[str] = None
    retries: Optional[int] = None


class StepDef(BaseModel):
    """
    A single step in the user’s plan.
    'node' can be a simple static node name, or a full NodeSpec.
    """
    name: str
    after: Optional[Union[str, List[str]]] = None
    exit_condition: Optional[str] = None
    branches: Optional[Dict[str, str]] = None
    node: Union[str, NodeSpec]


class BlueprintSpec(BaseModel):
    llms: List[LLMDef] = Field(default_factory=list)
    retrievers: List[RetrieverDef] = Field(default_factory=list)
    tools: List[ToolDef] = Field(default_factory=list)
    agents: List[AgentDef] = Field(default_factory=list)
    plan: List[StepDef]
