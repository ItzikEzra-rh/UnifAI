"""
Service for Slack channel operations orchestrating Slack API and Mongo repository.

Keeps persistence in Mongo repository and API logic here for reuse.
"""

from typing import Optional, Dict, Any
from shared.logger import logger
from utils.storage.mongo.mongo_helpers import get_mongo_storage
from config.constants import Database
from .slack_config import slack_event_config


class SlackChannelStorageService:
    """
    Orchestrates Slack channel persistence and API fetching.
    """

    def __init__(self):
        storage = get_mongo_storage()
        self._repo = storage.slack_channels
        self._conn = storage._conn
        self._db = Database.DATA_SOURCES.value
        self._collection_name = "slack_channels"

    def find_by_channel_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        return self._repo.find_by_channel_id(channel_id)

    def update_membership(self, channel_id: str, is_member: bool, timestamp: float) -> bool:
        return self._repo.update_membership(channel_id, is_member, timestamp)

    def insert_channel(self, channel_doc: Dict[str, Any]) -> bool:
        return self._repo.insert_channel(channel_doc)

    def get_or_create_channel(self, channel_id: str, is_member: bool, timestamp: float) -> bool:
        """
        Ensure a channel document exists with up-to-date membership info.
        """
        existing = self.find_by_channel_id(channel_id)
        if existing:
            return self.update_membership(channel_id, is_member, timestamp)

        return self._create_new_channel(channel_id, is_member, timestamp)

    def _create_new_channel(self, channel_id: str, is_member: bool, timestamp: float) -> bool:
        channel_doc = self._fetch_channel_from_api(channel_id, is_member)
        if not channel_doc:
            channel_doc = self._create_minimal_channel_doc(channel_id, is_member, timestamp)
        else:
            channel_doc["last_updated"] = timestamp

        return self.insert_channel(channel_doc)

    def _fetch_channel_from_api(self, channel_id: str, is_member: bool) -> Optional[Dict[str, Any]]:
        try:
            connector = slack_event_config.get_configured_connector()
            if not connector:
                return None

            response = connector._make_api_request("conversations.info", {"channel": channel_id})
            if not response.get("ok"):
                logger.warning(f"conversations.info failed for {channel_id}: {response.get('error', 'unknown')}")
                return None

            channel_info = response.get("channel") or {}
            return self._repo.create_channel_document(channel_info, connector._project_id, is_app_member=is_member)
        except Exception as e:
            logger.warning(f"API call failed for {channel_id}: {e}")
            return None

    def _create_minimal_channel_doc(self, channel_id: str, is_member: bool, timestamp: float) -> Dict[str, Any]:
        return {
            "channel_id": channel_id,
            "channel_name": f"Channel-{channel_id[-6:]}" if channel_id else "Unknown",
            "type": "Unknown",
            "is_private": None,
            "project_id": "no-project-configured",
            "is_app_member": is_member,
            "last_updated": timestamp,
            "created_from_event": True,
        }


