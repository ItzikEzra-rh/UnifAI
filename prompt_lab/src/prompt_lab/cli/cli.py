import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import click
from tasks import run_orbiter, run_landing, run_launchpad
from config import ConfigManager
from utils.celery.celery import start_celery_worker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CliContext:
    """Class to manage CLI context and configuration."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config_manager: Optional[ConfigManager] = None

    def initialize_config(self) -> None:
        """Initialize configuration manager."""
        if not self.config_path.exists():
            raise click.ClickException(f"Configuration file '{self.config_path}' does not exist.")
        self.config_manager = ConfigManager(str(self.config_path))
        logger.info(f"Initialized configuration from {self.config_path}")

    def update_config(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with provided overrides."""
        if self.config_manager is None:
            self.initialize_config()

        filtered_overrides = {key: value for key, value in overrides.items() if value is not None}
        self.config_manager.update(filtered_overrides)
        logger.debug(f"Updated configuration with: {filtered_overrides}")
        return self.config_manager.config


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
    """CLI for managing project tasks and configurations."""
    config_path = os.getenv('APP_CONFIG_PATH', config_path)
    ctx.ensure_object(dict)
    ctx.obj['CLI_CONTEXT'] = CliContext(config_path)


def common_options(command):
    """Decorator for common CLI options."""
    options = [
        click.option('--mongodb-ip', default="0.0.0.0", show_default=True, help="MongoDB IP for data handling."),
        click.option('--mongodb-port', default="27017", show_default=True, help="MongoDB Port for data handling."),
        click.option('--rabbitmq-ip', default="0.0.0.0", show_default=True, help="RabbitMQ IP for messaging."),
        click.option('--rabbitmq-port', default="5672", show_default=True, help="RabbitMQ Port for messaging."),
        click.option('--celery', is_flag=True, help="Run with Celery worker.")
    ]
    for option in reversed(options):
        command = option(command)
    return command


def handle_task(task_function, ctx: click.Context, kwargs: Dict[str, Any], queue_key: Optional[str] = None) -> None:
    """Common handler for CLI tasks."""
    # try:
    cli_context: CliContext = ctx.obj['CLI_CONTEXT']
    config = cli_context.update_config(kwargs)

    if kwargs.get("celery"):
        logger.info(f"Starting Celery worker for queue: {config.get(queue_key)}")
        start_celery_worker(queue_name=config.get(queue_key))
    else:
        logger.info(f"Starting task: {task_function.__name__}")
        task_function()
    # except Exception as e:
    #     logger.error(f"Task failed: {e}")
    #     raise click.ClickException(str(e))


@cli.command()
@common_options
@click.option('--tokenizer-path', help="Tokenizer repository ID.")
@click.option('--templates-path', help="Template path.")
@click.option('--model-max-context-length', type=int, help="Maximum context length for the model.")
@click.option('--model-max-generation-length', type=int, help="Maximum generation length for the model.")
@click.option('--batch-size', type=int, help="Batch size for prompts.")
@click.option('--orbiter-queue-name', help="Queue name for prompts.")
@click.option('--orbiter-task-name', help="Orbiter task name.")
@click.option('--orbiter-queue-target-size', help="Orbiter queue target size.")
@click.option('--input-dataset-repo', help="Input dataset repository ID.")
@click.option('--input-dataset-file-name', help="Input dataset file name in the repo.")
@click.option('--output-dataset-repo', help="Output dataset repository ID.")
@click.pass_context
def launchpad(ctx: click.Context, **kwargs: Any) -> None:
    """Prepare and enqueue prompts for processing."""
    handle_task(run_launchpad, ctx, kwargs)


@cli.command()
@common_options
@click.option('--tokenizer-path', help="Tokenizer repository ID.")
@click.option('--model-max-context-length', type=int, help="Maximum context length for the model.")
@click.option('--model-max-generation-length', type=int, help="Maximum generation length for the model.")
@click.option('--model-name', help="model name.")
@click.option('--model-api-url', help="LLM API URL.")
@click.option('--reviewer-queue-name', help="Reviewer queue name.")
@click.option('--reviewer-task-name', help="Reviewer task name.")
@click.option('--orbiter-queue-name', help="Orbiter queue name.")
@click.pass_context
def orbiter(ctx: click.Context, **kwargs: Any) -> None:
    """Query the LLM with prepared prompts."""
    handle_task(run_orbiter, ctx, kwargs, queue_key='orbiter_queue_name')


@cli.command()
@common_options
@click.option('--max-retry', type=int, help="Maximum retries for failed prompts.")
@click.option('--reviewed-prompts-queue-name', help="Reviewed prompts queue name.")
@click.option('--orbiter-queue-name', help="Orbiter queue name.")
@click.option('--orbiter-task-name', help="Orbiter task name.")
@click.pass_context
def landing(ctx: click.Context, **kwargs: Any) -> None:
    """Process and manage the results of LLM queries."""
    handle_task(run_landing, ctx, kwargs, queue_key='reviewed_prompts_queue_name')


if __name__ == "__main__":
    cli(auto_envvar_prefix='APP')
