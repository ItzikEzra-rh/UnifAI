from pydantic import BaseModel, Field, Extra
from typing import Literal, List, Optional, Union


class NodeBaseConfig(BaseModel):
    """
    Shared fields for all nodes.
    """
    name: Optional[str] = Field(
        None,
        description="Optional instance name for this node; falls back to type if unset"
    )

    class Config:
        extra = Extra.forbid  # forbid any fields not explicitly declared here


class MockAgentNodeConfig(NodeBaseConfig):
    """
    Allows overriding only the LLM key for the mock agent node.
    """
    type: Literal["mock_agent_node"] = "mock_agent_node"
    llm: Optional[str] = Field(
        None,
        description="Override default LLM key for this mock agent"
    )


class CustomAgentNodeConfig(NodeBaseConfig):
    """
    Full overrides for a custom agent node:
     - llm, retriever, tools, system_message, retries.
    """
    type: Literal["custom_agent_node"] = "custom_agent_node"
    llm: Optional[str] = Field(
        None, description="Override default LLM key"
    )
    retriever: Optional[str] = Field(
        None, description="Override default retriever key"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Override default list of tool keys"
    )
    system_message: Optional[str] = Field(
        None, description="Override default system prompt"
    )
    retries: Optional[int] = Field(
        None, description="Override default retry count"
    )


class FinalAnswerNodeConfig(NodeBaseConfig):
    """
    No overrides allowed—this node simply emits the final_output.
    """
    type: Literal["final_answer_node"] = "final_answer_node"


class UserQuestionNodeConfig(NodeBaseConfig):
    """
    No overrides allowed—this node just logs/passes through user_input.
    """
    type: Literal["user_question_node"] = "user_question_node"


NodeConfig = Union[
    MockAgentNodeConfig,
    CustomAgentNodeConfig,
    FinalAnswerNodeConfig,
    UserQuestionNodeConfig,
]


class NodesSpec(BaseModel):
    """
    A list of inline node definitions in the user blueprint.

    Uses `type` as the discriminator to pick the correct config subclass.
    """
    nodes: List[NodeConfig] = Field(
        ...,
        discriminator="type",
        description="Inline node specs with per-type override fields"
    )
