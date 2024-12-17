# Prompt Lab

Prompt Lab is a customizable prompt generation tool designed for projects requiring dynamic and flexible prompt creation
and processing. This tool can interact with Language Models (LLMs) to generate and process prompts based on user-defined
templates and configurations. Prompt Lab is equipped to handle diverse prompt types and integrates seamlessly with
storage solutions like MongoDB for managing generated prompts and responses.

## Project Structure

The project is organized into the following main components:

- **config/**: Contains configuration files necessary for setting up project-specific settings.

- **processing/**: Houses the core processing modules for generating and managing prompts.

- **storage/**: Implements the storage mechanisms for prompts and responses.

- **utils/**: Utility modules supporting various tasks within the project.

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

Prompt Lab supports customization through its configuration files. You can define new prompt templates or modify
existing ones by updating `project_config.json`. Additionally, you can extend storage capabilities by implementing new
repository classes within the `storage` directory.

## Contributing

Feel free to open issues or create pull requests if you'd like to contribute. We welcome suggestions and improvements to
make Prompt Lab even more robust and flexible.

## list of Models

meta-llama/Llama-3.1-8B-Instruct unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit

## VLLM command line to run model

--quantization bitsandbytes --load-format bitsandbytes are optional parameters which are required for quantized models

```bash
vllm serve model_repo_hf --port 8000 --max-model-len 8192 --quantization bitsandbytes --load-format bitsandbytes
```

** Here are the instructions, explaining how to use the Dockerfile of the reviewer component: **

# Building the image

podman build -t promptlab-service .

# To run promptlab worker:

```bash
podman run -d --name promptlab_worker --gpus all --net=host \
  -e INPUT_JSON_PATH="$INPUT_JSON_PATH" \
  -e OUTPUT_DATA_DIR_PATH="$OUTPUT_DATA_DIR_PATH" \
  -e RABBITMQ_PORT="$RABBITMQ_PORT" \
  -e RABBITMQ_IP="$RABBITMQ_IP" \
  -e MONGODB_PORT="$MONGODB_PORT" \
  -e MONGODB_IP="$MONGODB_IP" \
  promptlab-service prompt_processor
 ```

# To run promptlab dispatcher worker:

```bash
podman run -d --name prompt_dispatcher --gpus all --net=host \
  -e INPUT_JSON_PATH="$INPUT_JSON_PATH" \
  -e OUTPUT_DATA_DIR_PATH="$OUTPUT_DATA_DIR_PATH" \
  -e RABBITMQ_PORT="$RABBITMQ_PORT" \
  -e RABBITMQ_IP="$RABBITMQ_IP" \
  -e MONGODB_PORT="$MONGODB_PORT" \
  -e MONGODB_IP="$MONGODB_IP" \
  promptlab-service prompt_dispatcher
```

# To run promptlab handler worker:

```bash
podman run -d --name promptlab_handler --gpus all --net=host \
  -e INPUT_JSON_PATH="$INPUT_JSON_PATH" \
  -e OUTPUT_DATA_DIR_PATH="$OUTPUT_DATA_DIR_PATH" \
  -e RABBITMQ_PORT="$RABBITMQ_PORT" \
  -e RABBITMQ_IP="$RABBITMQ_IP" \
  -e MONGODB_PORT="$MONGODB_PORT" \
  -e MONGODB_IP="$MONGODB_IP" \
  promptlab-service prompt_submiter

```


# config params that is needed when running the containers:

```
INPUT_JSON_PATH
OUTPUT_DATA_DIR_PATH
RABBITMQ_PORT
RABBITMQ_IP
MONGODB_PORT
MONGODB_IP
PROMPT_LAB_MODEL_HF_ID
PROMPT_LAB_MAX_GENERATION_LENGTH
PROMPT_LAB_MAX_CONTEXT_LENGTH
PROMPT_LAB_BATCH_SIZE
QUEUE_TARGET_SIZE
TEMPLATE_PATH
TEMPLATE_AGENT
TEMPLATE_TYPE
```