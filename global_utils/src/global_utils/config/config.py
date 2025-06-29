from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, Callable
from .sources import DotEnvSource, YamlSource, JsonSource
from ..utils.singleton import SingletonMeta

SettingsSource = Callable[[], Dict[str, Any]]
    
class SharedConfig(BaseSettings, metaclass=SingletonMeta):
    """
    Anything every app needs.
    """
    mongodb_port: str = "27017"
    mongodb_ip: str = "ae8f0dd8e6cd046539c3f0b7c6a75f13-508991814.us-east-1.elb.amazonaws.com"
    rabbitmq_port: str = "5672"
    rabbitmq_ip: str = "a509af714a5fa4810bf879cfc8823456-1634716882.us-east-1.elb.amazonaws.com"
    
    # shared loading order
    model_config = SettingsConfigDict(
        env_prefix="",
        settings_customise_sources=lambda init, env, fs: (
            init,
            env,
            DotEnvSource().load,
            YamlSource().load,
            JsonSource().load,
            fs,
        ),
    )
