from pydantic import BaseModel
from typing import Literal, Dict, List


class SlackRetrieverConfig(BaseModel):
    """
    Configuration for a Slack-based retriever agent.
    """
    name: str
    type: Literal["slack"]
    vector_store: Dict[str, any]  # E.g. vector store parameters


class JiraRetrieverConfig(BaseModel):
    """
    Configuration for a Jira-based retriever agent.
    """
    name: str
    type: Literal["jira"]
    vector_store: Dict[str, any]


class PDFRetrieverConfig(BaseModel):
    """
    Configuration for a PDF-based retriever agent.
    """
    name: str
    type: Literal["pdf"]
    documents: List[str]  # List of filepaths or URIs to PDF documents
