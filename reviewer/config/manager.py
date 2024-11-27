import json
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.config = self.load_config()

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

    def validate(self):
        """
        Validate the configuration structure.
        """
        required_keys = [
            "storage_type",
            "input.file_path",
            "output.directory",
            "model_config.tokenizer_path",
            "model_config.model_name",
            "model_config.api_url",
            "rabbitmq.url",
            "mongodb.url",
        ]
        for key in required_keys:
            if self.get(key) is None:
                raise ValueError(f"Missing required configuration key: {key}")

        print("Configuration is valid.")


config = ConfigManager("config/config.json")