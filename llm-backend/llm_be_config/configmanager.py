from configparser import ConfigParser
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dr = os.path.join(os.path.dirname(curr_dir))
config_dir = os.path.join(os.path.dirname(curr_dir), 'llm_be_config')
config_file = os.path.join(config_dir, 'backend.cfg')


class ConfigManager(object):
    """
    class that is responsible for laoding config cfg file and its handling
    """

    def __init__(self, config_file_path):
        self.config = ConfigManager.load_config(config_file_path)

    @staticmethod
    def load_config(config_file_path):
        parser = ConfigParser()
        parser.read(config_file_path)
        return parser

    def get(self, section, key, default=None):
        try:
            return self.config.get(section, key)
        except Exception:
            return default

    def items(self):
        return self.config.items()


config = ConfigManager(config_file)
