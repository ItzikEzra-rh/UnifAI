from abc import ABC, abstractmethod
from typing import Any, List, Tuple


class ConfigurationManager(ABC):
    """
    Port: Configuration manager interface.
    
    Defines what configuration capabilities are needed by connectors.
    Implementations live in infrastructure.
    """
    
    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        pass
    
    @abstractmethod
    def set_config_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass

