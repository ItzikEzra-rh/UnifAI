from processing.data_processor import DataProcessor
from config.manager import config
from utils.util import load_json_config
from storage.file_data_repository import FileDataRepository


class DataProcessorFactory:
    """
    Factory for creating DataProcessor instances with standardized configuration.
    """

    def __init__(self):
        self.config = config
        self.configure_repository = FileDataRepository.configure_repository()

    def create(self) -> DataProcessor:
        project_config = self.config.get("templates.project_path")
        io_repository = self.configure_repository
        project_config = load_json_config(project_config)

        return DataProcessor(
            io_repository=io_repository,
            project_config=project_config,
            api_url=self.config.get('model_config.api_url'),
            model_name=self.config.get('model_config.model_name'),
            max_generation_length=self.config.get('model_config.max_generation_length'),
            max_context_length=self.config.get('model_config.max_context_length'),
            batch_size=self.config.get('prompt_lab.batch_size'),
            fetch_prompts_queue_target_size=self.config.get('prompt_lab.queues.fetch_prompts_queue.target_size'),
            fetch_prompts_queue_name=self.config.get('prompt_lab.queues.fetch_prompts_queue.name'),
        )
