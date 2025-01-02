import click


class BaseCommand:
    """Base class for CLI commands."""

    @staticmethod
    def get_command():
        raise NotImplementedError("Subclasses should implement this method.")


class ExampleCommand(BaseCommand):
    """An example command."""

    @staticmethod
    @click.command(name="example")
    def example():
        """Run the example command."""
        click.echo("Running example command!")

    @staticmethod
    def get_command():
        return ExampleCommand.example
