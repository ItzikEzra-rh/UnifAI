from typing import Dict, List, Tuple, Any, Optional
from shared.logger import logger
from pipeline.slack_pipeline_factory import SlackPipelineFactory
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from datetime import datetime


class WebhookSlackPipelineFactory(SlackPipelineFactory):
    """
    Incremental version of SlackPipelineFactory that only processes new messages
    since the last processed timestamp for a channel.
    """
    
    def __init__(self, metadata: Any):
        super().__init__(metadata)
        self.mongo_storage = get_mongo_storage()
    
    def get_last_processed_timestamp(self) -> Optional[str]:
        """
        Get the last processed timestamp for this channel.
        
        Returns:
            Last processed timestamp or None if never processed
        """
        # Check if we have timestamp tracking in the source record
        source_response = self.mongo_storage.get_source_info(self.metadata.channel_id)
        
        if source_response.get("success") and source_response.get("source_info"):
            source_info = source_response["source_info"]
            if source_info.get("type_data"):
                return source_info["type_data"].get("last_processed_timestamp")
        
        return None
    
    def update_last_processed_timestamp(self, timestamp: str) -> None:
        """
        Update the last processed timestamp for this channel.
        
        Args:
            timestamp: New timestamp to store
        """
        try:
            # Use existing mongo storage methods to update the source
            source_response = self.mongo_storage.get_source_info(self.metadata.channel_id)
            if source_response.get("success") and source_response.get("source_info"):
                current_source = source_response["source_info"]
                
                # Create updated type_data
                type_data = current_source.get("type_data", {})
                type_data.update({
                    "last_processed_timestamp": timestamp,
                    "last_incremental_update": datetime.now().isoformat()
                })
                
                # Update the source with new type_data
                self.mongo_storage.upsert_source_summary(
                    source_id=self.metadata.channel_id,
                    source_name=current_source.get("source_name", self.metadata.channel_name),
                    source_type=current_source.get("source_type", "SLACK"),
                    upload_by=current_source.get("upload_by", "default"),
                    pipeline_id=current_source.get("pipeline_id", ""),
                    type_data=type_data
                )
                logger.info(f"Updated last processed timestamp for channel {self.metadata.channel_id}: {timestamp}")
            else:
                logger.warning(f"Could not find source record for channel {self.metadata.channel_id}")
        except Exception as e:
            logger.error(f"Failed to update timestamp for channel {self.metadata.channel_id}: {str(e)}")
    
    def _create_collector(self) -> Tuple[List[Dict], List[List[Dict]]]:
        """
        Collect only incremental messages since last processed timestamp.
        
        Returns:
            Tuple of (messages, threads) containing only new messages
        """
        last_timestamp = self.get_last_processed_timestamp()
        
        if last_timestamp:
            logger.info(f"Fetching incremental messages for channel {self.metadata.channel_name} since {last_timestamp}")
            # Use the incremental method we added to SlackConnector
            messages, threads = self.connector.get_incremental_conversations_history(
                channel_id=self.metadata.channel_id,
                since_timestamp=last_timestamp
            )
        else:
            logger.info(f"No previous timestamp found for channel {self.metadata.channel_name}, fetching all messages")
            # First time processing this channel, get all messages
            messages, threads = self.connector.get_conversations_history(
                channel_id=self.metadata.channel_id
            )
        
        total_messages = len(messages) + sum(len(thread) for thread in threads)
        logger.info(f"Retrieved {len(messages)} new messages and {len(threads)} new threads "
                   f"({total_messages} total) for channel {self.metadata.channel_name}")
        
        # Store the messages for timestamp extraction later
        self._collected_messages = messages
        self._collected_threads = threads
        
        return messages, threads
    
    def _create_storage(self, embeddings: List[Dict]) -> Any:
        """
        Store embeddings and update the last processed timestamp.
        
        Args:
            embeddings: List of embeddings to store
            
        Returns:
            Storage result
        """
        # Store embeddings using the parent method
        result = super()._create_storage(embeddings)
        
        # Find and update the latest timestamp from processed messages
        latest_timestamp = self._find_latest_timestamp()
        if latest_timestamp:
            self.update_last_processed_timestamp(latest_timestamp)
        
        return result
    
    def _find_latest_timestamp(self) -> Optional[str]:
        """
        Find the latest timestamp from the collected messages.
        
        Returns:
            Latest timestamp as string or None if no messages
        """
        all_messages = []
        
        # Add main messages
        if hasattr(self, '_collected_messages'):
            all_messages.extend(self._collected_messages)
        
        # Add thread messages
        if hasattr(self, '_collected_threads'):
            for thread in self._collected_threads:
                all_messages.extend(thread)
        
        if not all_messages:
            return None
        
        # Extract timestamps and find the maximum
        timestamps = []
        for msg in all_messages:
            ts = msg.get("ts")
            if ts:
                try:
                    timestamps.append(float(ts))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid timestamp format: {ts}")
                    continue
        
        if not timestamps:
            return None
        
        return str(max(timestamps)) 