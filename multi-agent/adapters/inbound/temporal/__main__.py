"""
Temporal worker entry point — creates the container and passes it.

Usage:
    python -m inbound.temporal
    python -m inbound.temporal --threads 20
"""
import argparse
import asyncio

from mas.config.app_config import AppConfig
from bootstrap.container import AppContainer
from inbound.temporal.worker import run_worker


def main() -> None:
    parser = argparse.ArgumentParser(description="Temporal graph engine worker")
    parser.add_argument("--threads", type=int, default=10, help="Activity thread pool size")
    args = parser.parse_args()

    cfg = AppConfig.get_instance()
    container = AppContainer(cfg)
    asyncio.run(run_worker(container, args.threads))


main()
