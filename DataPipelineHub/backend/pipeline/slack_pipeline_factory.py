from functools import cached_property
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from pipeline.pipeline_factory import PipelineFactory
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from data_sources.slack.slack_data_processor import SlackProcessor
from data_sources.slack.slack_chunker_strategy import SlackChunkerStrategy
from shared.config import ChunkerConfig
from config.constants import DataSource
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from shared.logger import logger
import time
from config.app_config import AppConfig

class SlackPipelineFactory(PipelineFactory):
    SOURCE_TYPE = DataSource.SLACK.upper_name
    
    def __init__(
        self,
    ):
        super().__init__()
        self.app_config = AppConfig()

    def _get_configured_connector(self) -> SlackConnector:
        config_manager = SlackConfigManager()
        config_manager.set_project_tokens(
            project_id="example-project",
            bot_token=self.app_config.default_slack_bot_token,
            user_token=self.app_config.default_slack_user_token
        )
        config_manager.set_default_project("example-project")
        return SlackConnector(config_manager) 
    
    def _create_collector(self) -> SlackConnector:
        connector = self._get_configured_connector()
        if not connector.authenticate():
            raise RuntimeError("Slack authentication failed")
        return connector
    
    def _create_processor(self) -> SlackProcessor:
        return SlackProcessor()
    
    def _create_chunker(self) -> SlackChunkerStrategy:
            cfg = ChunkerConfig()
            return SlackChunkerStrategy(
                max_tokens_per_chunk=cfg.max_tokens_per_chunk,
                overlap_tokens=cfg.overlap_tokens,
                time_window_seconds=300
            )

    @cached_property
    def slack_chunker(self) -> SlackChunkerStrategy:
        cfg = ChunkerConfig()
        return SlackChunkerStrategy(
            max_tokens_per_chunk=cfg.max_tokens_per_chunk,
            overlap_tokens=cfg.overlap_tokens,
            time_window_seconds=300
        )

    def get_source_id(self) -> str:
        return self.metadata.channel_id

    def get_source_name(self) -> str:
        return self.metadata.channel_name
        
    def _create_summary(self) -> Dict:
        return {
            "is_private": self.metadata.is_private,
        }
        
    def _create_collector(self) -> Tuple[List[Dict], List[List[Dict]]]:
        # Get date range from user settings if available
        oldest_timestamp = self._get_date_range_oldest_timestamp()
        
        if oldest_timestamp:
            logger.info(f"Fetching messages for channel {self.metadata.channel_name} since {oldest_timestamp}")
            return self.connector.get_conversations_history(
                channel_id=self.metadata.channel_id,
                oldest=oldest_timestamp
            )
        else:
            logger.info(f"Fetching all messages for channel {self.metadata.channel_name} (no date range specified)")
            return self.connector.get_conversations_history(
                channel_id=self.metadata.channel_id
            )
    
    def _get_date_range_oldest_timestamp(self) -> Optional[str]:
        """
        Get the oldest timestamp from pre-stored start_timestamp datetime in type_data.
        
        Returns:
            Slack timestamp string or None if no timestamp specified
        """
        try:
            # Get source info from MongoDB to access stored datetime objects
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if not source_response.get("success") or not source_response.get("source_info"):
                logger.warning(f"Could not get source info for channel {self.metadata.channel_id}")
                return None
            
            source_info = source_response["source_info"]
            type_data = source_info.get("type_data", {})
            
            # Use stored start_timestamp datetime object
            start_timestamp_obj = type_data.get("start_timestamp")
            
            if start_timestamp_obj:
                # Convert datetime object to Slack timestamp format
                if isinstance(start_timestamp_obj, str):
                    # If it's stored as ISO string, parse it first
                    start_dt = datetime.fromisoformat(start_timestamp_obj.replace('Z', '+00:00'))
                else:
                    # If it's already a datetime object
                    start_dt = start_timestamp_obj
                
                timestamp_str = str(start_dt.timestamp())
                logger.info(f"Using stored start timestamp: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} → {timestamp_str}")
                return timestamp_str
            
            # Fallback: if no stored timestamp, try old date range logic
            date_range = type_data.get("dateRange")
            if date_range:
                logger.warning(f"No stored timestamp found, falling back to parsing dateRange: {date_range}")
                days_back = self._parse_date_range(date_range)
                if days_back is not None:
                    oldest_date = datetime.now() - timedelta(days=days_back)
                    oldest_timestamp = str(oldest_date.timestamp())
                    logger.info(f"Fallback calculation - Date range '{date_range}' converted to timestamp: {oldest_timestamp}")
                    return oldest_timestamp
            
            logger.info(f"No date range specified for channel {self.metadata.channel_id}, will fetch all messages")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get timestamp for channel {self.metadata.channel_id}: {str(e)}")
            return None
    
    def _parse_date_range(self, date_range: str) -> Optional[int]:
        """
        Parse date range string from UI into number of days.
        
        Args:
            date_range: String like "30 days", "90 days", "1 year", etc.
            
        Returns:
            Number of days to go back or None if invalid
        """
        if not date_range:
            return None
        
        date_range = date_range.lower().strip()
        
        # Handle common formats
        if "30 days" in date_range or "30days" in date_range:
            return 30
        elif "60 days" in date_range or "60days" in date_range:
            return 60
        elif "90 days" in date_range or "90days" in date_range:
            return 90
        elif "6 months" in date_range or "6months" in date_range:
            return 180
        elif "1 year" in date_range or "1year" in date_range:
            return 365
        elif "all time" in date_range or "alltime" in date_range:
            return None  # No limit
        else:
            # Try to extract number + unit
            import re
            match = re.search(r'(\d+)\s*(day|days|month|months|year|years)', date_range)
            if match:
                number = int(match.group(1))
                unit = match.group(2)
                
                if unit.startswith('day'):
                    return number
                elif unit.startswith('month'):
                    return number * 30
                elif unit.startswith('year'):
                    return number * 365
            
            logger.warning(f"Unable to parse date range: {date_range}")
            return None

    def _create_processor(
        self,
        data: Tuple[List[Dict], List[List[Dict]]],
    ) -> Tuple[List[Dict], List[List[Dict]]]:
        messages, threads = data
        slack_processor = SlackProcessor()
        main = slack_processor.process(
            messages, channel_name=self.metadata.channel_name
        )
        thrs = [
            slack_processor.process(t, channel_name=self.metadata.channel_name)
            for t in threads
        ]
        return main, thrs

    def _create_chunker_and_embedder(
        self,
        processed: Tuple[List[Dict], List[List[Dict]]],
    ) -> List[Dict]:
        main, threads = processed
        chunks = self.slack_chunker.chunk_content(main)
        chunker = self.slack_chunker
        for t in threads:
            chunks.extend(chunker.chunk_content(t))

        for idx, c in enumerate(chunks):
            md = c.setdefault("metadata", {})
            md.update({
                "source_id":    self.metadata.channel_id,
                "chunk_index":  idx,
                "source_type":  DataSource.SLACK.upper_name,
            })

        return self.embedder.generate_embeddings(chunks)
