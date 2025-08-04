from typing import Dict, List, Tuple, Optional
from datetime import datetime
from shared.logger import logger
from pipeline.slack_pipeline_factory import SlackPipelineFactory
from utils.storage.mongo.mongo_helpers import get_mongo_storage


class WebhookSlackPipelineFactory(SlackPipelineFactory):
    """
    Incremental version of SlackPipelineFactory for daily webhook processing.
    
    This factory:
    1. Respects the original user's date range selection for boundaries
    2. Only processes new messages since the last processed timestamp
    3. Updates the timestamp tracking after successful processing
    """
    
    def get_last_processed_timestamp(self) -> Optional[str]:
        """
        Get the last processed timestamp for this channel.
        
        Returns:
            Last processed timestamp or None if never processed
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if source_response.get("success") and source_response.get("source_info"):
                source_info = source_response["source_info"]
                type_data = source_info.get("type_data", {})
                return type_data.get("last_processed_timestamp")
            
            return None
        except Exception as e:
            logger.error(f"Failed to get last processed timestamp for channel {self.metadata.channel_id}: {str(e)}")
            return None
    
    def update_last_processed_timestamp(self, timestamp: str) -> None:
        """
        Update the last processed timestamp for this channel.
        
        Args:
            timestamp: New timestamp to store
        """
        try:
            mongo_storage = get_mongo_storage()
            source_response = mongo_storage.get_source_info(self.metadata.channel_id)
            
            if source_response.get("success") and source_response.get("source_info"):
                current_source = source_response["source_info"]
                
                # Update type_data with new timestamp
                type_data = current_source.get("type_data", {})
                type_data.update({
                    "last_processed_timestamp": timestamp,
                    "last_incremental_update": datetime.now().isoformat()
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
                logger.info(f"Updated last processed timestamp for channel {self.metadata.channel_id}: {timestamp}")
            else:
                logger.warning(f"Could not find source record for channel {self.metadata.channel_id}")
                
        except Exception as e:
            logger.error(f"Failed to update timestamp for channel {self.metadata.channel_id}: {str(e)}")
    
    def _create_collector(self) -> Tuple[List[Dict], List[List[Dict]]]:
        """
        Collect only incremental messages since last processed timestamp,
        but still respect the original user's date range as a boundary.
        
        Returns:
            Tuple of (messages, threads) containing only new messages
        """
        # Get the last processed timestamp for incremental processing
        last_processed_timestamp = self.get_last_processed_timestamp()
        
        # Get the original date range boundary (oldest allowed timestamp)
        original_oldest_timestamp = self._get_date_range_oldest_timestamp()
        
        # Determine the effective oldest timestamp to use
        if last_processed_timestamp:
            # For incremental processing, use the last processed timestamp
            # but respect the original date range as a boundary
            if original_oldest_timestamp:
                # If we have both, use the more recent one (larger timestamp)
                # This ensures we don't go beyond the user's original date range
                if float(last_processed_timestamp) >= float(original_oldest_timestamp):
                    oldest_timestamp = last_processed_timestamp
                    logger.info(f"Using incremental timestamp: {last_processed_timestamp}")
                else:
                    # If last processed is older than date range, use date range
                    oldest_timestamp = original_oldest_timestamp
                    logger.info(f"Last processed timestamp is older than date range, using date range: {original_oldest_timestamp}")
            else:
                # No original date range, just use last processed
                oldest_timestamp = last_processed_timestamp
                logger.info(f"Using incremental timestamp (no date range): {last_processed_timestamp}")
        else:
            # First time processing this channel, use original date range if available
            oldest_timestamp = original_oldest_timestamp
            if oldest_timestamp:
                logger.info(f"First time processing, using date range: {oldest_timestamp}")
            else:
                logger.info(f"First time processing, fetching all messages for channel {self.metadata.channel_name}")
        
        # Fetch incremental messages
        if oldest_timestamp:
            logger.info(f"Fetching incremental messages for channel {self.metadata.channel_name} since {oldest_timestamp}")
            messages, threads = self.connector.get_incremental_conversations_history(
                channel_id=self.metadata.channel_id,
                since_timestamp=oldest_timestamp
            )
        else:
            logger.info(f"Fetching all messages for channel {self.metadata.channel_name}")
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
    
    def _create_storage(self, embeddings: List[Dict]) -> any:
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
        
        # Return the latest timestamp as string
        return str(max(timestamps))