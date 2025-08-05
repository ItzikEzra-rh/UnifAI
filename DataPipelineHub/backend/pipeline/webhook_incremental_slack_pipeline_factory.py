from typing import Dict, List, Tuple, Optional
from datetime import datetime
from shared.logger import logger
from pipeline.slack_pipeline_factory import SlackPipelineFactory
from utils.storage.mongo.mongo_helpers import get_mongo_storage


class WebhookIncrementalSlackPipelineFactory(SlackPipelineFactory):
    """
    Webhook-based incremental version of SlackPipelineFactory.
    
    This factory:
    1. Fetches only new messages since the last embedding timestamp
    2. Does not use webhook counter (that's managed by the cron job)
    3. Updates the last embedding timestamp after successful processing
    """
    
    def _create_collector(self) -> Tuple[List[Dict], List[List[Dict]]]:
        """
        Collect only new messages since the last embedding timestamp, but respect original date range boundaries.
        
        Returns:
            Tuple of (messages, threads) containing only new messages
        """
        # Get the last embedding timestamp for incremental processing
        last_embedding_timestamp = self._get_last_embedding_timestamp()
        
        # Determine the appropriate timestamp to use
        if last_embedding_timestamp:
            # Use last embedding timestamp for subsequent runs
            oldest_timestamp = last_embedding_timestamp
            logger.info(f"Fetching messages for channel {self.metadata.channel_name} since last embedding: {oldest_timestamp}")
        else:
            # First time processing - use the original date range start_timestamp
            oldest_timestamp = self._get_original_start_timestamp()
            if oldest_timestamp:
                logger.info(f"First webhook embedding for channel {self.metadata.channel_name}, using original date range: {oldest_timestamp}")
            else:
                logger.warning(f"No date range found for channel {self.metadata.channel_name}, fetching all messages")
        
        # Fetch messages with the determined timestamp
        if oldest_timestamp:
            messages, threads = self.connector.get_incremental_conversations_history(
                channel_id=self.metadata.channel_id,
                since_timestamp=oldest_timestamp
            )
        else:
            # Fallback: fetch all messages (should rarely happen)
            messages, threads = self.connector.get_conversations_history(
                channel_id=self.metadata.channel_id
            )
        
        total_messages = len(messages) + sum(len(thread) for thread in threads)
        logger.info(f"Retrieved {len(messages)} new messages and {len(threads)} new threads "
                   f"({total_messages} total) for channel {self.metadata.channel_name}")
        
        # Store messages for timestamp extraction later
        self._collected_messages = messages
        self._collected_threads = threads
        
        return messages, threads
    
    def _get_last_embedding_timestamp(self) -> Optional[str]:
        """
        Get the last embedding timestamp for this channel.
        
        Returns:
            Last embedding timestamp or None if never embedded
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if source_response.get("success") and source_response.get("source_info"):
                source_info = source_response["source_info"]
                type_data = source_info.get("type_data", {})
                return type_data.get("last_embedding_timestamp")
            
            return None
        except Exception as e:
            logger.error(f"Failed to get last embedding timestamp for channel {self.metadata.channel_id}: {str(e)}")
            return None
    
    def _get_original_start_timestamp(self) -> Optional[str]:
        """
        Get the original start_timestamp from the channel's initial date range selection.
        
        Returns:
            Start timestamp from original date range or None if not found
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if source_response.get("success") and source_response.get("source_info"):
                source_info = source_response["source_info"]
                type_data = source_info.get("type_data", {})
                
                # Get the stored start_timestamp datetime object
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
                    logger.info(f"Using original start timestamp: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} → {timestamp_str}")
                    return timestamp_str
                
                # Fallback: try to get from dateRange if start_timestamp is missing
                date_range = type_data.get("dateRange")
                if date_range:
                    logger.warning(f"No start_timestamp found, falling back to parsing dateRange: {date_range}")
                    # This would require importing the date calculation logic, but for now log the issue
                    logger.error(f"Missing start_timestamp for channel {self.metadata.channel_id}, cannot determine date range")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get original start timestamp for channel {self.metadata.channel_id}: {str(e)}")
            return None
    
    def _create_storage(self, embeddings: List[Dict]) -> any:
        """
        Store embeddings and update the last embedding timestamp.
        
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
            self._update_last_embedding_timestamp(latest_timestamp)
        
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
        
        # Return the latest timestamp as string
        return str(max(timestamps))
    
    def _update_last_embedding_timestamp(self, timestamp: str) -> None:
        """
        Update the last embedding timestamp for this channel.
        
        Args:
            timestamp: New embedding timestamp to store
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if source_response.get("success") and source_response.get("source_info"):
                current_source = source_response["source_info"]
                
                # Update type_data with new embedding timestamp
                type_data = current_source.get("type_data", {})
                type_data.update({
                    "last_embedding_timestamp": timestamp,
                    "last_embedding_date": datetime.now().isoformat()
                })
                
                # Update the source with new type_data
                mongo_storage.upsert_source_summary(
                    source_id=self.metadata.channel_id,
                    source_name=current_source.get("source_name", self.metadata.channel_name),
                    source_type=current_source.get("source_type", "SLACK"),
                    upload_by=current_source.get("upload_by", "system"),
                    pipeline_id=current_source.get("pipeline_id", ""),
                    type_data=type_data
                )
                logger.info(f"Updated last embedding timestamp for channel {self.metadata.channel_id}: {timestamp}")
            else:
                logger.warning(f"Could not find source record for channel {self.metadata.channel_id}")
                
        except Exception as e:
            logger.error(f"Failed to update embedding timestamp for channel {self.metadata.channel_id}: {str(e)}")