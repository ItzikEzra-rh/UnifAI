from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import SlackRetrieverConfig
from ..slack_retriever_factory import SlackRetrieverFactory


class SlackRetrieverElementSpec(BaseElementSpec):
    """Element specification for Slack Retriever."""

    category = ResourceCategory.RETRIEVER
    type_key = "slack"
    name = "Slack Retriever"
    description = "Fetches recent messages matching a query from Slack"
    config_schema = SlackRetrieverConfig
    factory_cls = SlackRetrieverFactory
    tags = ["retriever", "slack", "search", "query", "information retrieval"]
