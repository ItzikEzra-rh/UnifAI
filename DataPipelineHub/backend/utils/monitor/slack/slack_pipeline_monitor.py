
from typing import Dict, List
from ..pipeline_monitor_base import SourceType
from ..pipeline_monitor import PipelineMonitor

class SlackPipelineMonitor:
    """
    Specialized monitor for Slack pipelines.
    
    This class extends the base monitoring capabilities with Slack-specific features.
    """
    
    def __init__(self, monitor: PipelineMonitor):
        """
        Initialize the Slack pipeline monitor.
        
        Args:
            monitor: The base pipeline monitor instance
        """
        self.monitor = monitor
    
    def get_channel_stats(self, channel_id: str) -> Dict:
        """
        Get statistics for a specific Slack channel.
        
        Args:
            channel_id: The ID of the Slack channel
            
        Returns:
            Dictionary containing channel statistics
        """
        pipeline_id = f"slack_{channel_id}"
        return self.monitor.get_pipeline_stats(pipeline_id)
    
    def get_all_slack_stats(self) -> Dict:
        """
        Get aggregated statistics for all Slack pipelines.
        
        Returns:
            Dictionary containing aggregated Slack statistics
        """
        return self.monitor.get_source_stats(SourceType.SLACK)
    
    def get_active_channels(self) -> List[Dict]:
        """
        Get all active Slack channel pipelines.
        
        Returns:
            List of active Slack pipeline dictionaries
        """
        return self.monitor.get_active_pipelines(SourceType.SLACK)
    
    def get_recent_slack_activity(self, limit: int = 10) -> List[str]:
        """
        Get recent log entries for Slack pipelines.
        
        Args:
            limit: Maximum number of log entries to return
            
        Returns:
            List of log message strings
        """
        return self.monitor.get_recent_activity(SourceType.SLACK, limit)
