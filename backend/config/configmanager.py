from configparser import ConfigParser
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dr = os.path.join(os.path.dirname(curr_dir))
config_dir = os.path.join(os.path.dirname(curr_dir), 'config')
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
        with open(config_file_path, 'r') as cfg_file:
               cfg_txt = os.path.expandvars(cfg_file.read())

        parser.read_string(cfg_txt)
        return parser

    def get(self, section, key, default=None):
        try:
            return self.config.get(section, key)
        except Exception:
            return default

    def items(self):
        return self.config.items()


config = ConfigManager(config_file)
