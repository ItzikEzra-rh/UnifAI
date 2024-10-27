import json
from storage.file_data_repository import FileDataRepository
# from storage.mongo_data_repository import MongoDataRepository
from processing.data_processor import DataProcessor


def load_json_config(file_path):
    """Load JSON configuration from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)


def configure_repository(config):
    """Configure the repository based on config and repo_type."""
    storage_type = config['storage_type']

    if storage_type == 'file':
        return FileDataRepository(
            input_file_path=config['input']['file_path'],
            output_directory=config['output']['directory']
        )
    return None  # Default to None if not configured


# Main Processing Function
def main():
    # Load configurations
    config = load_json_config('config/config.json')
    project_config = load_json_config('config/project_config.json')

    # Configure repositories for input and output
    io_repository = configure_repository(config)

    # Initialize Data Processor
    data_processor = DataProcessor(
        io_repository=io_repository,
        project_config=project_config,
        api_url=config['model_config']['api_url'],
        model_name=config["model_config"]["model_name"],
        max_generation_length=config["model_config"]["max_generation_length"],
        max_context_length=config["model_config"]["max_context_length"],
        batch_size=config['model_config']['batch_size']
    )

    # Start processing
    data_processor.process_all_elements()


if __name__ == "__main__":
    main()
