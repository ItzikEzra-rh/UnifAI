from typing import ClassVar, Literal, Union, Annotated, Protocol
from pydantic import BaseModel, Field, Extra, HttpUrl, SkipValidation


# Protocol for retriever metadata
class RetrieverMeta(Protocol):
    category: ClassVar[str]
    display_name: ClassVar[str]
    description: ClassVar[str]
    type: ClassVar[str]


# Base retriever config with shared fields and default Meta
class BaseRetrieverConfig(BaseModel):
    """
    Common fields for any Retriever.
    Subclasses must set `type` Literal and can override Meta.
    """
    name: str = Field(..., description="Unique key for this retriever instance")
    type: str = Field(
        ..., description="Discriminator: which retriever provider to use"
    )

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    class Meta(RetrieverMeta):
        category:      ClassVar[SkipValidation[str]] = "retriever"
        display_name:  ClassVar[SkipValidation[str]] = "Generic Retriever"
        description:   ClassVar[SkipValidation[str]] = "Base configuration for all retrievers"
        type:          ClassVar[SkipValidation[str]] = "base"


# Slack retriever config with metadata
class SlackRetrieverConfig(BaseRetrieverConfig):
    """
    Retrieves messages from Slack via an API endpoint.
    """
    type: Literal["slack"] = "slack"
    api_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://0.0.0.0:13456/api/slack/query.match"),
        description="URL for retrieving slack messages from the API"
    )
    top_k_results: int = Field(
        3, ge=1,
        description="Number of top Slack messages to return"
    )
    threshold: float = Field(
        0.3, ge=0.0, le=1.0,
        description="Minimum relevance score to include a message"
    )

    class Meta(BaseRetrieverConfig.Meta):
        category:      ClassVar[SkipValidation[str]] = "retriever"
        display_name:  ClassVar[SkipValidation[str]] = "Slack Retriever"
        description:   ClassVar[SkipValidation[str]] = "Fetches recent messages matching a query from Slack"
        type:          ClassVar[SkipValidation[str]] = "slack"


# Docs retriever config with metadata
class DocsRetrieverConfig(BaseRetrieverConfig):
    """
    Retrieves document passages via an API endpoint.
    """
    type: Literal["docs"] = "docs"
    api_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://0.0.0.0:13456/api/docs/query.match"),
        description="URL for retrieving docs from the API"
    )
    top_k_results: int = Field(
        3, ge=1,
        description="Number of top document passages to return"
    )
    threshold: float = Field(
        0.3, ge=0.0, le=1.0,
        description="Minimum relevance score to include a passage"
    )

    class Meta(BaseRetrieverConfig.Meta):
        category:      ClassVar[SkipValidation[str]] = "retriever"
        display_name:  ClassVar[SkipValidation[str]] = "Docs Retriever"
        description:   ClassVar[SkipValidation[str]] = "Fetches relevant document passages for a query"
        type:          ClassVar[SkipValidation[str]] = "docs"


# Discriminated union for retriever specifications
RetrieversSpec = Annotated[
    Union[SlackRetrieverConfig, DocsRetrieverConfig],
    Field(discriminator="type")
]
