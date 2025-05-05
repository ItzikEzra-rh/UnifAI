from pydantic import BaseModel, Field, Extra
from typing import Literal, List, Optional, Union, Annotated


class NodeBaseConfig(BaseModel):
    """
    Defines all atomic node fields as optional.
    Subclasses will override required ones as needed.
    """
    name: Optional[str] = Field(None, description="Optional node instance name")
    llm: Optional[str] = Field(None, description="LLM key to use")
    retriever: Optional[str] = Field(None, description="Retriever key to use")
    tools: List[str] = Field(default_factory=list, description="List of tool keys")
    system_message: Optional[str] = Field(None, description="Custom system prompt")
    retries: Optional[int] = Field(None, description="Retry count if failure")

    class Config:
        extra = Extra.forbid


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
        1, description="Override default retry count"
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


# Apply discriminator correctly to the union
NodeSpec = Annotated[
    Union[
        MockAgentNodeConfig,
        CustomAgentNodeConfig,
        FinalAnswerNodeConfig,
        UserQuestionNodeConfig,
    ],
    Field(discriminator="type")
]
