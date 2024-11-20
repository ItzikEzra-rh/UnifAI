import json
from storage.file_data_repository import FileDataRepository
# from storage.mongo_data_repository import MongoDataRepository
from processing.data_processor import DataProcessor
from config.manager import config


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def configure_repository():
    """Configure the repository based on config and repo_type."""
    storage_type = config.get('storage_type')

    if storage_type == 'file':
        return FileDataRepository(
            input_file_path=config.get('input.file_path'),
            output_directory=config.get('output.directory')
        )
    return None  # Default to None if not configured


# Main Processing Function
def main():
    # Load configurations
    project_config = config.get("templates.project_path")

    # Configure repositories for input and output
    io_repository = configure_repository()

    # Initialize Data Processor
    data_processor = DataProcessor(
        io_repository=io_repository,
        project_config=project_config,
        api_url=config.get('model_config.api_url'),
        model_name=config.get('model_config.model_name'),
        max_generation_length=config.get('model_config.max_generation_length'),
        max_context_length=config.get('model_config.max_context_length'),
        batch_size=config.get('model_config.batch_size')
    )

    # Start processing
    data_processor.process_all_elements()


if __name__ == "__main__":
    main()
