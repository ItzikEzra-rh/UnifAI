from .configmanager import config
import os


def add_constants():
    def adder(cls):
        for config_section in config.items():
            config_section_name = config_section[0]
            config_section_param_list = config_section[1]

            if config_section_name != 'DEFAULT':
                for attribute in config_section_param_list:
                    full_param_name = ''.join([config_section_name.upper(), '_', attribute.upper()])
                    param_value = config.get(config_section_name, attribute)
                    setattr(cls, full_param_name, param_value)

        return cls

    return adder


@add_constants()
class ConfigParams():
    """ class that is responsible for parsing all the attributes from config_file """

    def get_param_by_env(self, param):
        print(param)
        print(os.environ)
        full_param_name = ''.join([os.environ['BACKEND_ENV'].upper(), '_', param.upper()])
        return config_params.__getattribute__(full_param_name)


# Create one object of the class for the whole project  
config_params = ConfigParams()
