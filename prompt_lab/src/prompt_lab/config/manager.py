import json
from pathlib import Path


class ConfigManager:
    _instance = None  # Class-level attribute to store the singleton instance

    def __new__(cls, config_path="config/config.json"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path="config/config.json"):
        if self._initialized:  # Avoid reinitializing the singleton instance
            return
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self._initialized = True

    def load_config(self):
        """
        Load configuration from the file.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")

        with self.config_path.open("r") as f:
            return json.load(f)

    def save_config(self):
        """
        Save the current configuration back to the file.
        """
        with self.config_path.open("w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        """
        Get a configuration value using dot notation.
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_as_int(self, key, default=None):
        value = self.get(key, default)
        return int(value) if value is not None else default

    def get_as_bool(self, key, default=None):
        value = self.get(key, default)
        return bool(value) if value is not None else default

    def set(self, key, value):
        """
        Set a configuration value using dot notation.
        """
        keys = key.split(".")
        config_section = self.config
        for k in keys[:-1]:
            if k not in config_section:
                config_section[k] = {}
            config_section = config_section[k]
        config_section[keys[-1]] = value
        self.save_config()

    def update(self, updates):
        """
        Bulk update configuration with a dictionary of values.
        """
        for key, value in updates.items():
            self.set(key, value)
