from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Extra, HttpUrl, ConfigDict


class BaseRetrieverConfig(BaseModel):
    """
    Common fields for any Retriever.
    Concrete configs must subclass this and set `type` to a Literal.
    """
    name: str = Field(..., description="Unique key for this retriever instance")
    type: str = Field(..., description="Discriminator: which retriever provider to use")

    class Config:
        extra = Extra.forbid


class SlackRetrieverConfig(BaseRetrieverConfig):
    type: Literal["slack"] = "slack"
    api_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://0.0.0.0:13456/api/slack/query.match"),
        description="URL for retrieving slack messages from the API"
    )
    top_k_results: int = Field(3, ge=1)
    threshold: float = Field(0.3, ge=0.0, le=1.0)


class DocsRetrieverConfig(BaseRetrieverConfig):
    type: Literal["docs"] = "docs"
    api_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://0.0.0.0:13456/api/docs/query.match"),
        description="URL for retrieving docs from the API"
    )
    top_k_results: int = Field(3, ge=1)
    threshold: float = Field(0.3, ge=0.0, le=1.0)


RetrieversSpec = Annotated[
    Union[DocsRetrieverConfig, SlackRetrieverConfig],
    Field(discriminator="type")
]
