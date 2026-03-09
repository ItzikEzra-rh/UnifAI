"""
Temporal client factory.

Provides an async function to connect to the Temporal server
using configuration from AppConfig.

Shared by both inbound (worker) and outbound (executor/submitter)
Temporal adapters.
"""
from temporalio.client import Client

from mas.config.app_config import AppConfig


async def get_temporal_client() -> Client:
    cfg = AppConfig.get_instance()
    return await Client.connect(
        cfg.temporal_host,
        namespace=cfg.temporal_namespace,
    )
