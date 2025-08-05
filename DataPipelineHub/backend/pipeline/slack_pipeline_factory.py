from functools import cached_property
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from pipeline.pipeline_factory import PipelineFactory
from shared.source_types import SlackMetadata
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
        metadata: SlackMetadata,
    ):
        super().__init__(metadata)
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
    
    @cached_property
    def connector(self) -> SlackConnector:
        connector = self._get_configured_connector()
        if not connector.authenticate():
            raise RuntimeError("Slack authentication failed")
        return connector

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
        Get the oldest timestamp based on user's date range selection.
        
        Returns:
            Slack timestamp string or None if no date range specified
        """
        try:
            # Get source info from MongoDB to access user settings
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if not source_response.get("success") or not source_response.get("source_info"):
                return None
            
            source_info = source_response["source_info"]
            type_data = source_info.get("type_data", {})
            date_range = type_data.get("dateRange")
            
            if not date_range:
                return None
            
            # Parse date range and convert to timestamp
            days_back = self._parse_date_range(date_range)
            if days_back is None:
                return None
            
            # Calculate timestamp for X days ago
            oldest_date = datetime.now() - timedelta(days=days_back)
            # Convert to Slack timestamp format (seconds since epoch with microseconds)
            oldest_timestamp = str(oldest_date.timestamp())
            
            logger.info(f"Date range '{date_range}' converted to timestamp: {oldest_timestamp} ({oldest_date})")
            return oldest_timestamp
            
        except Exception as e:
            logger.warning(f"Failed to get date range for channel {self.metadata.channel_id}: {str(e)}")
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
