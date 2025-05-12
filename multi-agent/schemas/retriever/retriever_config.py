from typing import Literal
from pydantic import Field, Extra, BaseModel, HttpUrl


class BaseRetrieverConfig(BaseModel):
    """
    Common fields for any Retriever.
    Concrete configs must subclass this and set `type` to a Literal.
    """
    name: str = Field(
        ...,
        description="Unique key for this retriever instance"
    )
    type: str = Field(
        ...,
        description="Discriminator: which retriever provider to use"
    )

    class Config:
        extra = Extra.forbid


class SlackRetrieverConfig(BaseRetrieverConfig):
    """
    Pydantic schema for the SlackRetriever.
    """
    type: Literal["slack"] = "slack"
    api_url: HttpUrl = Field(
        "http://0.0.0.0:13456/api/slack/query.match",
        description="The endpoint for your Slack‐query service"
    )
    top_k_results: int = Field(
        3,
        ge=1,
        description="How many top matches to request"
    )
    threshold: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Minimum score to accept a match"
    )

    class Config:
        extra = Extra.forbid
