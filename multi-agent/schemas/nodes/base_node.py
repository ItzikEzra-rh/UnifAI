from typing import ClassVar, Literal, List, Optional, Union, Annotated, Protocol
from pydantic import BaseModel, Field, Extra, SkipValidation


# Protocol for node metadata
class NodeMeta(Protocol):
    category: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]


class NodeUserMeta(BaseModel):
    description: Optional[str] = Field(None, description="Short title or label for the node instance")
    display_name: Optional[str] = Field(None, description="Custom description for this node's purpose")
    tags: Optional[List[str]] = Field(default_factory=list, description="User-defined tags for categorization")


# Base node config with shared fields and default Meta
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
    retries: Optional[int] = Field(1, description="Retry count if failure")
    meta: Optional[NodeUserMeta] = Field(None, description="User-defined metadata for this node instance")

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(NodeMeta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "Base Node"
        description: ClassVar[SkipValidation[str]] = "Abstract base for all node configs"
        type: ClassVar[SkipValidation[str]] = "base"


# Specific node configs with metadata
class MockAgentNodeConfig(NodeBaseConfig):
    """
    Allows overriding only the LLM key for the mock agent node.
    """
    type: Literal["mock_agent_node"] = "mock_agent_node"
    llm: Optional[str] = Field(
        None,
        description="Override default LLM key for this mock agent"
    )

    class Meta(NodeBaseConfig.Meta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "Mock Agent Node"
        description: ClassVar[SkipValidation[str]] = "Returns mock responses for testing"
        type: ClassVar[SkipValidation[str]] = "mock_agent_node"


class CustomAgentNodeConfig(NodeBaseConfig):
    """
    Custom agent node with full override capabilities.
    """
    type: Literal["custom_agent_node"] = "custom_agent_node"

    class Meta(NodeBaseConfig.Meta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "Custom Agent Node"
        description: ClassVar[SkipValidation[str]] = "Agent node with LLM, retriever, tools, and prompt overrides"
        type: ClassVar[SkipValidation[str]] = "custom_agent_node"


class MergerLLMNodeConfig(NodeBaseConfig):
    """
    Node that merges outputs from multiple agents.
    """
    type: Literal["merger_node"] = "merger_node"

    class Meta(NodeBaseConfig.Meta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "Merger Node"
        description: ClassVar[SkipValidation[str]] = "Aggregates and synthesizes agent outputs"
        type: ClassVar[SkipValidation[str]] = "merger_node"


class FinalAnswerNodeConfig(NodeBaseConfig):
    """
    Emits the final aggregated answer without overrides.
    """
    type: Literal["final_answer_node"] = "final_answer_node"

    class Meta(NodeBaseConfig.Meta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "Final Answer Node"
        description: ClassVar[SkipValidation[str]] = "Outputs the final response"
        type: ClassVar[SkipValidation[str]] = "final_answer_node"


class UserQuestionNodeConfig(NodeBaseConfig):
    """
    Logs or passes through user input without modification.
    """
    type: Literal["user_question_node"] = "user_question_node"

    class Meta(NodeBaseConfig.Meta):
        category: ClassVar[SkipValidation[str]] = "node"
        display_name: ClassVar[SkipValidation[str]] = "User Question Node"
        description: ClassVar[SkipValidation[str]] = "Captures and forwards the user’s question"
        type: ClassVar[SkipValidation[str]] = "user_question_node"


# Discriminated union for node specifications
NodeSpec = Annotated[
    Union[
        MockAgentNodeConfig,
        CustomAgentNodeConfig,
        MergerLLMNodeConfig,
        FinalAnswerNodeConfig,
        UserQuestionNodeConfig,
    ],
    Field(discriminator="type")
]
