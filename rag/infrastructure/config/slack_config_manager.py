from typing import Dict, List, Optional, Any, Tuple
from domain.connector.configuration import ConfigurationManager


class SlackConfigManager(ConfigurationManager):
    """
    Configuration manager for Slack integration.
    
    Manages Slack-specific configuration and credentials, including OAuth tokens.
    """
    
    def __init__(self):
        """Initialize the Slack configuration manager."""
        self._config: Dict[str, Any] = {}
        self._project_tokens: Dict[str, Dict[str, str]] = {}
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate Slack-specific configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if we have at least one project configured
        if not self._project_tokens:
            errors.append("No project tokens configured")
        
        # Check each project's configuration
        for project_id, tokens in self._project_tokens.items():
            if not tokens.get('bot_token'):
                errors.append(f"Missing bot token for project {project_id}")
        
        return len(errors) == 0, errors
    
    def set_project_tokens(self, project_id: str, user_token: Optional[str] = None, 
                         bot_token: Optional[str] = None) -> None:
        """
        Set OAuth tokens for a specific project.
        
        Args:
            project_id: The project identifier
            user_token: User OAuth token
            bot_token: Bot User OAuth token
        """
        if project_id not in self._project_tokens:
            self._project_tokens[project_id] = {}
        
        if user_token:
            self._project_tokens[project_id]['user_token'] = user_token
        
        if bot_token:
            self._project_tokens[project_id]['bot_token'] = bot_token
        
        # Update the configuration dictionary
        self._config['project_tokens'] = self._project_tokens
    
    def get_project_tokens(self, project_id: str) -> Dict[str, str]:
        """
        Get OAuth tokens for a specific project.
        
        Args:
            project_id: The project identifier
            
        Returns:
            Dictionary containing user_token and bot_token
        
        Raises:
            KeyError: If project_id doesn't exist
        """
        if project_id not in self._project_tokens:
            raise KeyError(f"No tokens configured for project {project_id}")
        
        return self._project_tokens[project_id]
    
    def get_default_project(self) -> Optional[str]:
        """
        Get the default project ID.
        
        Returns:
            The default project ID or None if not set
        """
        return self.get_config_value('default_project')
    
    def set_default_project(self, project_id: str) -> None:
        """
        Set the default project ID.
        
        Args:
            project_id: The project identifier to set as default
        """
        if project_id not in self._project_tokens:
            raise KeyError(f"Cannot set default project to {project_id}; not in project tokens")
        
        self.set_config_value('default_project', project_id)
