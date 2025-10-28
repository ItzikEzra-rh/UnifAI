"""
Slack event configuration management.

Centralizes configuration setup for Slack event processing.
"""

from typing import Optional
from data_sources.slack.slack_config_manager import SlackConfigManager
from data_sources.slack.slack_connector import SlackConnector
from config.app_config import AppConfig
from shared.logger import logger


class SlackEventConfig:
    """
    Manages Slack configuration for event processing.
    
    Provides a consistent way to configure SlackConnector across all event handlers.
    """
    
    _instance: Optional['SlackEventConfig'] = None
    _config_manager: Optional[SlackConfigManager] = None
    
    def __new__(cls) -> 'SlackEventConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_configured_connector(self) -> Optional[SlackConnector]:
        """
        Get a configured SlackConnector instance.
        
        Returns:
            SlackConnector or None if configuration fails
        """
        try:
            if self._config_manager is None:
                self._setup_config()
            
            return SlackConnector(self._config_manager)
            
        except Exception as e:
            logger.warning(f"Failed to create configured SlackConnector: {e}")
            return None
    
    def _setup_config(self) -> None:
        """Setup SlackConfigManager with project tokens."""
        try:
            self._config_manager = SlackConfigManager()
            app_config = AppConfig()
            
            # Configure project tokens (same pattern as SlackPipelineFactory)
            self._config_manager.set_project_tokens(
                project_id="example-project",
                bot_token=app_config.default_slack_bot_token,
                user_token=app_config.default_slack_user_token
            )
            self._config_manager.set_default_project("example-project")
            
            logger.info("Slack event configuration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Slack event configuration: {e}")
            raise


# Global instance for easy access
slack_event_config = SlackEventConfig()
