from typing import Any, Dict, Callable, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from .sources import DotEnvSource, YamlSource, JsonSource

typedef_SettingsSource = Callable[[], Dict[str, Any]]


class AppConfig(BaseSettings):
    """
    Application configuration.

    Priority order (highest→lowest):
      1) __init__ kwargs
      2) OS environment
      3) .env file
      4) config.yaml
      5) config.json
      6) file‑secrets
    """
    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017/"
    mongo_db: str = "UnifAI"
    blueprint_coll: str = "blueprints"
    session_coll: str = "workflow_sessions"
    hostname: str = "0.0.0.0"
    port: str = "8002"

    # Engine
    engine_name: str = "langgraph"

    model_config = SettingsConfigDict(
        env_file=None,
        settings_customise_sources=lambda init, env, fs: (
            init,
            env,
            DotEnvSource().load,
            YamlSource().load,
            JsonSource().load,
            fs,
        )
    )
