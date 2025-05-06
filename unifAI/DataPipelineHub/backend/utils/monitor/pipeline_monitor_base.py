"""
Pipeline Monitor Module for Data Pipeline Orchestration Layer.

This module provides comprehensive monitoring capabilities for data pipelines,
tracking execution statistics, errors, and progress across different data sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum


class PipelineStatus(Enum):
    """Enum representing possible pipeline statuses."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DONE = "DONE"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class SourceType(Enum):
    """Enum representing different data source types."""
    SLACK = "SLACK"
    JIRA = "JIRA"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"


class PipelineMonitorBase(ABC):
    """
    Abstract base class for pipeline monitoring implementations.
    
    This class defines the interface that all pipeline monitors must implement,
    ensuring consistent monitoring capabilities across different data sources.
    """
    
    @abstractmethod
    def register_pipeline(self, pipeline_id: str, source_type: SourceType) -> None:
        """Register a new pipeline in the monitoring system."""
        pass
    
    @abstractmethod
    def update_pipeline_status(self, pipeline_id: str, status: PipelineStatus) -> None:
        """Update the status of a pipeline."""
        pass
    
    @abstractmethod
    def log_metrics(self, pipeline_id: str, metrics: Dict[str, Any]) -> None:
        """Log performance metrics for a pipeline."""
        pass
    
    @abstractmethod
    def record_error(self, pipeline_id: str, error_message: str, error_details: Optional[Dict] = None) -> None:
        """Record an error that occurred during pipeline execution."""
        pass
    
    @abstractmethod
    def get_active_pipelines(self, source_type: Optional[SourceType] = None) -> List[Dict]:
        """Get all active pipelines, optionally filtered by source type."""
        pass
    
    @abstractmethod
    def get_pipeline_stats(self, pipeline_id: str) -> Dict:
        """Get comprehensive statistics for a specific pipeline."""
        pass
    
    @abstractmethod
    def get_source_stats(self, source_type: SourceType) -> Dict:
        """Get aggregated statistics for a specific source type."""
        pass
    
    @abstractmethod
    def get_recent_activity(self, source_type: SourceType, limit: int = 10) -> List[str]:
        """Get recent log entries for a specific source type."""
        pass
