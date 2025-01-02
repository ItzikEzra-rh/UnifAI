import click
from tasks import run_prepare, run_query, run_result
# from prompt_lab.utils.celery.celery import start_celery_worker
from config import ConfigManager


@click.group()
@click.option('--config-path', type=click.Path(exists=True), default="config/config.json",
              help="Path to the config file.")
@click.pass_context
def cli(ctx, config_path):
    """
    Main CLI for the project.
    """
    ctx.ensure_object(dict)

    # Load config into the context
    ctx.obj["CONFIG_MANAGER"] = ConfigManager(config_path)


def override_config(ctx, **overrides):
    """
    Override configuration values with CLI parameters.

    Args:
        ctx: Click context containing the ConfigManager instance.
        overrides: CLI parameters to override in the config.

    Returns:
        dict: Updated configuration.
    """
    config_manager = ctx.obj["CONFIG_MANAGER"]

    # Filter out None values and update the config
    filtered_overrides = {key: value for key, value in overrides.items() if value is not None}
    config_manager.update(filtered_overrides)

    return config_manager.config


@cli.command()
@click.option('--tokenizer-path', type=str, help="Tokenizer repository ID.")
@click.option('--model-max-context-length', type=int, help="Maximum context length for the model.")
@click.option('--model-max-generation-length', type=int, help="Maximum generation length for the model.")
@click.option('--batch-size', type=int, help="Batch size for prompts.")
@click.option('--fetch-prompts-queue-target-size', type=int, help="Queue target size.")
@click.option('--fetch-prompts-queue-name', type=str, help="Queue name for prompts.")
@click.option('--input-dataset-repo', type=str, help="Input dataset repository ID.")
@click.option('--output-dataset-repo', type=str, help="Output dataset repository ID.")
@click.option('--mongodb_ip', type=str, help="MongoDB IP for data handling.")
@click.option('--mongodb_port', type=str, help="MongoDB Port for data handling.")
@click.option('--celery', is_flag=True, help="Run with Celery.")
@click.pass_context
def prepare(ctx, **kwargs):
    """
    Prepare and enqueue prompts.
    """
    override_config(ctx, **kwargs)

    if kwargs.get("celery"):
        # start_celery_worker()
        pass
    else:
        run_prepare()


@cli.command()
@click.option('--model-api-url', type=str, help="LLM API URL.")
@click.option('--celery', is_flag=True, help="Run with Celery.")
@click.pass_context
def query(ctx, **kwargs):
    """
    Query the LLM with prepared prompts.
    """
    config = override_config(ctx, **kwargs)

    if kwargs.get("celery"):
        # start_celery_worker()
        pass
    else:
        run_query(config)


@cli.command()
@click.option('--max-retry', type=int, help="Maximum number of retries for failed prompts.")
@click.option('--celery', is_flag=True, help="Run with Celery.")
@click.pass_context
def result(ctx, **kwargs):
    """
    Process and manage the results of the LLM queries.
    """
    config = override_config(ctx, **kwargs)

    if kwargs.get("celery"):
        # start_celery_worker()
        pass
    else:
        run_result(config)


if __name__ == "__main__":
    cli()
