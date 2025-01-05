"""
CLI interface for managing and running project tasks.
Provides commands for launching prompts, querying LLM, and processing results.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import click
from tasks import run_orbiter, run_landing, run_launchpad
from config import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CliContext:
    """Class to manage CLI context and configuration."""

    def __init__(self, config_path: str):
        """Initialize CLI context with config path."""
        self.config_path = Path(config_path)
        self.config_manager: Optional[ConfigManager] = None

    def initialize_config(self) -> None:
        """Initialize configuration manager."""
        try:
            if not self.config_path.exists():
                raise click.ClickException(
                    f"Configuration file '{self.config_path}' does not exist."
                )
            self.config_manager = ConfigManager(str(self.config_path))
            logger.info(f"Initialized configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            raise

    def update_config(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration with provided overrides.

        Args:
            overrides: Dictionary of configuration values to override

        Returns:
            Updated configuration dictionary
        """
        if self.config_manager is None:
            self.initialize_config()

        filtered_overrides = {
            key: value for key, value in overrides.items()
            if value is not None
        }

        try:
            self.config_manager.update(filtered_overrides)
            logger.debug(f"Updated configuration with: {filtered_overrides}")
            return self.config_manager.config
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise


@click.group()
@click.option(
    '--config-path',
    type=click.Path(exists=False),
    default="config/config.json",
    help="Path to the configuration file.",
    show_default=True
)
@click.pass_context
def cli(ctx: click.Context, config_path: str) -> None:
    """
    Command-line interface for managing project tasks.

    Provides commands for launching prompts, querying LLM, and processing results.
    Configuration can be specified via --config-path or environment variable APP_CONFIG_PATH.
    """
    # Override config path from environment if set
    config_path = os.getenv('APP_CONFIG_PATH', config_path)
    logger.debug(f"Using configuration from: {config_path}")

    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['CLI_CONTEXT'] = CliContext(config_path)


def celery_worker_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    """Handle Celery worker initialization if needed."""
    if value:
        logger.info("Initializing Celery worker...")
        # start_celery_worker()
    return value


@cli.command()
@click.option(
    '--mongodb-ip',
    default="0.0.0.0",
    show_default=True,
    help="MongoDB IP for data handling."
)
@click.option(
    '--mongodb-port',
    default="27017",
    show_default=True,
    help="MongoDB Port for data handling."
)
@click.option(
    '--celery',
    is_flag=True,
    callback=celery_worker_callback,
    help="Run with Celery worker."
)
@click.option('--tokenizer-path', help="Tokenizer repository ID.")
@click.option('--model-max-context-length', type=int, help="Maximum context length for the model.")
@click.option('--model-max-generation-length', type=int, help="Maximum generation length for the model.")
@click.option('--batch-size', type=int, help="Batch size for prompts.")
@click.option('--fetch-prompts-queue-target-size', type=int, help="Queue target size.")
@click.option('--fetch-prompts-queue-name', help="Queue name for prompts.")
@click.option('--input-dataset-repo', help="Input dataset repository ID.")
@click.option('--input-dataset-file-name', default=None, help="Input dataset file name")
@click.option('--output-dataset-repo', help="Output dataset repository ID.")
@click.option('--templates-path', help="Template path")
@click.option('--templates-agent', help="Template agent name")
@click.option('--templates-type', help="Template type")
@click.pass_context
def launchpad(ctx: click.Context, **kwargs: Any) -> None:
    """Prepare and enqueue prompts for processing."""
    try:
        cli_context: CliContext = ctx.obj['CLI_CONTEXT']
        cli_context.update_config(kwargs)

        if not kwargs.get("celery"):
            logger.info("Starting launchpad task...")
            run_launchpad()
    except Exception as e:
        logger.error(f"Launchpad task failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--model-api-url', help="LLM API URL.")
@click.option(
    '--celery',
    is_flag=True,
    callback=celery_worker_callback,
    help="Run with Celery worker."
)
@click.pass_context
def orbiter(ctx: click.Context, **kwargs: Any) -> None:
    """Query the LLM with prepared prompts."""
    try:
        cli_context: CliContext = ctx.obj['CLI_CONTEXT']
        config = cli_context.update_config(kwargs)

        if not kwargs.get("celery"):
            logger.info("Starting orbiter task...")
            run_orbiter(config)
    except Exception as e:
        logger.error(f"Orbiter task failed: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--max-retry', type=int, help="Maximum number of retries for failed prompts.")
@click.option(
    '--celery',
    is_flag=True,
    callback=celery_worker_callback,
    help="Run with Celery worker."
)
@click.pass_context
def result(ctx: click.Context, **kwargs: Any) -> None:
    """Process and manage the results of LLM queries."""
    try:
        cli_context: CliContext = ctx.obj['CLI_CONTEXT']
        config = cli_context.update_config(kwargs)

        if not kwargs.get("celery"):
            logger.info("Starting result processing task...")
            run_landing(config)
    except Exception as e:
        logger.error(f"Result processing task failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli(auto_envvar_prefix='APP')
