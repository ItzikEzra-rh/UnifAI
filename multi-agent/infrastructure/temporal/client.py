"""
Temporal client factory.

Provides an async function to connect to the Temporal server
using configuration from AppConfig.
"""
from temporalio.client import Client


async def get_temporal_client() -> Client:
    from config.app_config import AppConfig

    cfg = AppConfig.get_instance()
    return await Client.connect(
        cfg.temporal_host,
        namespace=cfg.temporal_namespace,
    )
