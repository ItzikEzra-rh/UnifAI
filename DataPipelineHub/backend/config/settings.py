import os
from enum import Enum

class Database(Enum):
    """Database names"""
    DATA = "data_sources"
    PIPELINE = "pipeline_monitoring"

class Collection(Enum):
    """Collection names"""
    SOURCES = "sources"
    CHUNKS = "chunks"
    PIPELINES = "pipelines"

class DataSource(Enum):
    """Data source types with consistent naming"""
    SLACK = "slack"
    JIRA = "jira"
    DOCUMENT = "document"
    OTHER = "other"

    @property
    def upper_name(self) -> str:
        """Get uppercase name for legacy compatibility"""
        return self.value.upper()
    