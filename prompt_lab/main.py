import json
from storage.file_data_repository import FileDataRepository
# from storage.mongo_data_repository import MongoDataRepository
from processing.data_processor import DataProcessor
from utils.tokenizer import TokenizerUtils


def main():
    with open('config/config.json', 'r') as config_file:
        config = json.load(config_file)

    with open('config/project_config.json', 'r') as project_file:
        project_config = json.load(project_file)

    input_repository = None
    output_repository = None
    # Configure Input Repository
    if config['input_storage_type'] == 'file':
        input_repository = FileDataRepository(config['input_file_path'])
    # else:
    #     input_repository = MongoDataRepository(
    #         config['mongo_input_collection'],
    #         config['mongo_progress_collection'],
    #         config['mongo_output_collection'],
    #         project_config['project_id']
    #     )

    # Configure Output Repository
    if config['output_storage_type'] == 'file':
        output_repository = FileDataRepository(config['output_file_path'])
    # else:
    #     output_repository = MongoDataRepository(
    #         config['mongo_input_collection'],
    #         config['mongo_progress_collection'],
    #         config['mongo_output_collection'],
    #         project_config['project_id']
    #     )

    tokenizer = TokenizerUtils(config['tokenizer_path'])
    data_processor = DataProcessor(input_repository,
                                   output_repository,
                                   tokenizer,
                                   project_config,
                                   config['api_url'],
                                   config["max_context_length"])

    data_processor.process_all_elements()


if __name__ == "__main__":
    main()
