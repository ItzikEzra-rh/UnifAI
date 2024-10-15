
# Prompt Lab

Prompt Lab is a customizable prompt generation tool designed for projects requiring dynamic and flexible prompt creation and processing. This tool can interact with Language Models (LLMs) to generate and process prompts based on user-defined templates and configurations. Prompt Lab is equipped to handle diverse prompt types and integrates seamlessly with storage solutions like MongoDB for managing generated prompts and responses.

## Project Structure

The project is organized into the following main components:

- **config/**: Contains configuration files necessary for setting up project-specific settings.
  - `config.json`: General configuration for the application.
  - `project_config.json`: Specific configurations related to the project templates and prompts.

- **processing/**: Houses the core processing modules for generating and managing prompts.
  - `data_processor.py`: Manages the processing logic, orchestrating prompt generation and handling.
  - `llm_requester.py`: Interacts with an LLM to send requests and retrieve responses.

- **storage/**: Implements the storage mechanisms for prompts and responses.
  - `data_repository.py`: Abstract class defining the interface for data storage.
  - `file_data_repository.py`: Handles file-based storage of prompt data.
  - `mongo_data_repository.py`: Manages MongoDB storage for prompt data.

- **utils/**: Utility modules supporting various tasks within the project.
  - `mongo_handler.py`: Provides MongoDB connectivity and handling functions.
  - `tokenizer.py`: Includes tokenization utilities for processing text data.

- **main.py**: The entry point for running the application.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd prompt_lab
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MongoDB (optional, if you plan to use MongoDB for data storage).

## Usage

1. Configure your project settings in `config/config.json` and `config/project_config.json`.
2. Run the main application:
   ```bash
   python main.py
   ```

## Customization

Prompt Lab supports customization through its configuration files. You can define new prompt templates or modify existing ones by updating `project_config.json`. Additionally, you can extend storage capabilities by implementing new repository classes within the `storage` directory.

## Contributing

Feel free to open issues or create pull requests if you'd like to contribute. We welcome suggestions and improvements to make Prompt Lab even more robust and flexible.


