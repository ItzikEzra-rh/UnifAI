import requests
import time
import pymongo
from typing import Dict, List, Optional, Any, Tuple
from shared.logger import logger
from .slack_config_manager import SlackConfigManager
from utils.data_connector import DataConnector
from .slack_thread_retriever import SlackThreadRetriever
from .slack_thread_retriever_worker import ThreadRetrieverWorker
from global_utils.utils.util import get_mongo_url

class SlackConnector(DataConnector):
    """
    Connector for retrieving data from Slack.
    
    Handles authentication, rate limiting, and pagination for Slack API calls.
    """
    
    def __init__(self, config_manager: SlackConfigManager, project_id: Optional[str] = None):
        """
        Initialize the Slack connector.
        
        Args:
            config_manager: Configuration manager for Slack
            project_id: Optional project ID to use, defaults to the default project
        """
        super().__init__(config_manager)
        self.base_url = "https://slack.com/api/"
        self._available_apis = [
            "users.profile.get",
            "conversations.history",
            "conversations.list",
            "conversations.replies",
            "files.info",
        ]
        
        # Set the project ID
        self._project_id = project_id or config_manager.get_default_project()
        if not self._project_id:
            raise ValueError("No project ID provided and no default project set")
        
        # Get tokens for the project
        try:
            tokens = config_manager.get_project_tokens(self._project_id)
            self._user_token = tokens.get('user_token')
            self._bot_token = tokens.get('bot_token')
            
            if not self._bot_token:
                raise ValueError(f"Bot token not configured for project {self._project_id}")
                
        except KeyError as e:
            raise ValueError(f"Project tokens not found: {str(e)}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Slack API using configured tokens.
        
        Returns:
            True if authentication succeeds, False otherwise
        """
        try:
            # Test authentication by calling the auth.test endpoint
            response = self._make_api_request("auth.test")
            
            if response.get('ok'):
                logger.info(f"Successfully authenticated with Slack as {response.get('user')}")
                return True
            else:
                logger.error(f"Slack authentication failed: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Slack authentication error: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Slack API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        return self.authenticate()
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                          method: str = "GET", use_user_token: bool = False) -> Dict[str, Any]:
        """
        Make a request to the Slack API with rate limiting handling.
        
        Args:
            endpoint: The API endpoint (without base URL)
            params: Optional parameters to send with the request
            method: HTTP method to use (GET or POST)
            use_user_token: Whether to use the user token instead of the bot token
            
        Returns:
            The response from the API as a dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        token = self._user_token if use_user_token else self._bot_token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Track retry attempts
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                logger.info(f"Making API request to Slack endpoint: {endpoint}")
                
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params)
                else:  # POST
                    response = requests.post(url, headers=headers, json=params)
                
                response_data = response.json()
                
                # Check for rate limiting
                if not response_data.get('ok') and response_data.get('error') == 'ratelimited':
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited by Slack API. Retrying in {retry_after} seconds.")
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                
                if not response_data.get('ok'):
                    logger.error(f"Slack API error: {response_data.get('error')}")
                else:
                    logger.info(f"Slack API request to {endpoint} successful")
                    
                return response_data
                
            except Exception as e:
                logger.error(f"Error making request to Slack API {endpoint}: {str(e)}")
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retry_count += 1
                else:
                    raise
        
        # This should not be reached under normal circumstances
        raise Exception("Maximum retries exceeded when calling Slack API")
    
    def fetch_available_slack_channels(self) -> List[Dict[str, str]]:
        """
        Fetch all available Slack channels (both public and private) and cache them in MongoDB.
        This function fetches all channels without API call limits and stores them in the database.
        
        Returns:
            List of dictionaries containing channel_id, channel_name, and type
        """
        channels = []
        cursor = None
        api_call_count = 0
        
        # Get MongoDB connection
        mongo_client = pymongo.MongoClient(get_mongo_url())
        db = mongo_client["data_sources"]
        collection = db["slack_channels"]
        
        # Clear existing channels for this project to avoid duplicates
        collection.delete_many({"project_id": self._project_id})
        
        # Fetch all channels (both public and private) until there's no next_cursor
        while True:
            params: Dict[str, Any] = {"limit": 1000, "types": "public_channel,private_channel"}
            if cursor:
                params['cursor'] = cursor
            
            response = self._make_api_request("conversations.list", params)
            api_call_count += 1
            
            if not response.get('ok'):
                logger.error(f"Failed to get channels: {response.get('error')}")
                break
            
            # Process channels from current page
            batch_channels = []
            for channel in response.get('channels', []):
                channel_data = {
                    'channel_id': channel.get('id'),
                    'channel_name': channel.get('name'),
                    'type': 'Private' if channel.get('is_private', False) else 'Public',
                    'is_private': channel.get('is_private', False),
                    'project_id': self._project_id,
                    'last_updated': time.time()
                }
                channels.append(channel_data)
                batch_channels.append(channel_data)
            
            # Insert batch into MongoDB
            if batch_channels:
                collection.insert_many(batch_channels)
                logger.info(f"Cached {len(batch_channels)} channels to MongoDB")
            
            # Check if there are more pages
            response_metadata = response.get('response_metadata', {})
            cursor = response_metadata.get('next_cursor')
            
            # If no next_cursor or it's empty, we've reached the end
            if not cursor:
                break
        
        logger.info(f"Retrieved and cached {len(channels)} Slack channels from {api_call_count} API calls")
        return channels
    
    def get_available_slack_channels(self, types: Optional[str] = None, cursor: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get available Slack channels from cache (MongoDB) with pagination support.
        This function reads from the cached channels without making API calls.
        
        Args:
            types: Optional channel types to filter by ('private_channel', 'public_channel', or 'private_channel,public_channel')
            cursor: Optional cursor for pagination (skip count)
            limit: Number of channels to return (default: 50)
            
        Returns:
            Dictionary containing paginated channels data with pagination metadata
        """
        try:
            # Get MongoDB connection
            mongo_client = pymongo.MongoClient(get_mongo_url())
            db = mongo_client["data_sources"]
            collection = db["slack_channels"]
            
            # Build query filter
            query_filter: Dict[str, Any] = {"project_id": self._project_id}
            
            if types:
                # Convert types to cache types for querying
                channel_types = [t.strip() for t in types.split(',')]
                cache_types = []
                for channel_type in channel_types:
                    if channel_type == "private_channel":
                        cache_types.append("Private")
                    elif channel_type == "public_channel":
                        cache_types.append("Public")
                    else:
                        cache_types.append(channel_type)  # fallback
                query_filter['type'] = {"$in": cache_types}
            
            # Get total count for pagination metadata
            total_count = collection.count_documents(query_filter)
            
            # Calculate skip value from cursor
            skip = 0
            if cursor:
                try:
                    skip = int(cursor)
                except ValueError:
                    logger.warning(f"Invalid cursor value: {cursor}, using 0")
                    skip = 0
            
            # Fetch channels from cache with pagination
            cached_channels = list(collection.find(query_filter, {'_id': 0})
                                 .skip(skip)
                                 .limit(limit))
            
            # Calculate next cursor and hasMore
            next_cursor = None
            has_more = False
            
            if len(cached_channels) == limit and (skip + limit) < total_count:
                next_cursor = str(skip + limit)
                has_more = True
            
            logger.info(f"Retrieved {len(cached_channels)} Slack channels from cache (page {skip}-{skip+limit} of {total_count})")
            
            return {
                'channels': cached_channels,
                'nextCursor': next_cursor,
                'hasMore': has_more,
                'total': total_count,
            }
            
        except Exception as e:
            logger.error(f"Error retrieving channels from cache: {str(e)}")
            logger.warning("Falling back to API call with limited results")
            
            # Fallback to API call with limited results if cache fails
            fallback_channels = self._fallback_get_channels(types, max_api_calls=5)
            
            # Transform fallback response to paginated format
            start_idx = skip if cursor else 0
            end_idx = start_idx + limit
            paginated_channels = fallback_channels[start_idx:end_idx]
            
            return {
                'channels': paginated_channels,
                'nextCursor': str(end_idx) if end_idx < len(fallback_channels) else None,
                'hasMore': end_idx < len(fallback_channels),
                'total': len(fallback_channels),
            }
    
    def _fallback_get_channels(self, types: Optional[str] = None, max_api_calls: int = 5) -> List[Dict[str, str]]:
        """
        Fallback method to get channels directly from API with limited calls.
        Used when cache retrieval fails.
        
        Args:
            types: Optional channel types to filter by (e.g., 'private_channel', 'public_channel')
            max_api_calls: Maximum number of API calls to make
            
        Returns:
            List of dictionaries containing channel_id, channel_name, and is_private
        """
        channels = []
        cursor = None
        api_call_count = 0
        
        while api_call_count < max_api_calls:
            params: Dict[str, Any] = {"limit": 1000}
            if types:
                params['types'] = types
            if cursor:
                params['cursor'] = cursor
            
            response = self._make_api_request("conversations.list", params)
            api_call_count += 1
            
            if not response.get('ok'):
                logger.error(f"Failed to get channels: {response.get('error')}")
                break
            
            # Process channels from current page
            for channel in response.get('channels', []):
                channels.append({
                    'channel_id': channel.get('id'),
                    'channel_name': channel.get('name'),
                    'type': 'Private' if channel.get('is_private', False) else 'Public',
                    'is_private': channel.get('is_private', False),
                    'project_id': self._project_id,
                    'last_updated': time.time()
                })
            
            # Check if there are more pages
            response_metadata = response.get('response_metadata', {})
            cursor = response_metadata.get('next_cursor')
            
            # If no next_cursor or it's empty, we've reached the end
            if not cursor:
                break
        
        logger.info(f"Retrieved {len(channels)} Slack channels from {api_call_count} fallback API calls")
        return channels
    
    def get_conversations_history(self, channel_id: str, limit: int = 1000, 
                               cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[List[Dict[str, Any]]]]:
        """
        Get conversation history for a Slack channel with pagination handling and concurrently fetches thread replies.
        
        Args:
            channel_id: The ID of the channel to fetch history for
            limit: Maximum number of messages to return per page
            cursor: Pagination cursor from a previous request
        
        Returns:
            List of message objects from the conversation history
        """
        all_messages = []
        current_cursor = cursor
        has_more = True
        page = 1

        thread_retriever = SlackThreadRetriever(self)
        thread_worker = ThreadRetrieverWorker(thread_retriever)
        
        while has_more:
            params = {
                'channel': channel_id,
                'limit': limit
            }
            
            if current_cursor:
                params['cursor'] = current_cursor
            
            logger.info(f"Fetching conversation history (page {page}) for channel {channel_id}")
            response = self._make_api_request("conversations.history", params)
            
            if not response.get('ok'):
                logger.error(f"Failed to get conversation history: {response.get('error')}")
                break
                
            messages = response.get('messages', [])
            all_messages.extend(messages)
            logger.info(f"Retrieved {len(messages)} messages from channel {channel_id}")

            # Slack's conversations.history API only includes top-level messages in a channel, thread_replies aren't included in the response
            for msg in messages:
                # If the message is the parent of a thread, submit it to the thread worker queue
                if msg.get("thread_ts") == msg.get("ts"):
                    thread_worker.submit(channel_id, msg["ts"])
            
            # Check if there are more messages to fetch
            response_metadata = response.get('response_metadata', {})
            current_cursor = response_metadata.get('next_cursor')
            has_more = bool(current_cursor and response.get('has_more', False))
            page += 1
        
        logger.info(f"Retrieved a total of {len(all_messages)} messages from channel {channel_id}")
        
        # TODO: Consider whether to return directly 'thread_worker' under 'return' (in order to not block this entire function by calling thread_worker.gather_results()) 
        thread_messages = thread_worker.gather_results()
        logger.info(f"Retrieved a total of {len(thread_messages)} threads from channel {channel_id}")

        return all_messages, thread_messages