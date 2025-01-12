# PromptLab CLI

## Overview
PromptLab is a Command-Line Interface (CLI) tool for managing Prompt Lab operations, such as preparing prompts, querying a Large Language Model (LLM), and processing the results. It uses `Click` for command management, allowing various configurations and tasks.

---

## Table of Contents
1. [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Install Using `setup.py`](#install-using-setuppy)
   - [Install Using Docker](#install-using-docker)
2. [Using PromptLab CLI](#using-promptlab-cli)
   - [Available Commands](#available-commands)
   - [Common Options](#common-options)
   - [Command Details](#command-details)

---

## Installation

### Prerequisites
Ensure your system meets the following requirements:
1. **Python**: Version 3.9 or later.
2. **pip**: Installed for managing Python packages.

### Install Using `setup.py`

#### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd <repository-folder>
```

#### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install the Package
```bash
pip install .
```

#### Step 4: Verify Installation
After installation, verify that `promptlab` is accessible by running:
```bash
promptlab --help
```
This should display a list of available commands.

---

### Install Using Docker

#### Step 1: Build the Docker Image
Inside the project directory (where the `Dockerfile` is located), run:
```bash
docker build -t promptlab-cli .
```

#### Step 2: Run the Docker Container
To run the CLI inside a container, use the following command:
```bash
docker run -it --rm promptlab-cli --help
```

#### Environment Variables
When running in Docker, environment variables are loaded into the config file. If a variable is missing, it defaults to `None`. To provide custom environment variables, use the `-e` flag:
```bash
docker run -it --rm \
    -e INPUT_DATASET_REPO=my-dataset-repo \
    -e RABBITMQ_IP=127.0.0.1 \
    promptlab-cli <command>
```

---

## Using PromptLab CLI

### Available Commands
The CLI provides the following commands:
1. **`launchpad`**: Prepare and enqueue prompts for processing.
2. **`orbiter`**: Query the LLM with prepared prompts.
3. **`landing`**: Process and manage the results of LLM queries.

### Common Options
These options can be added to any command:
- `--config-path`: Path to the configuration file.
- `--log-level`: Logging level (e.g., `debug`, `info`, `warning`, `error`, `critical`).
- `--mongodb-ip` and `--mongodb-port`: MongoDB connection details.
- `--rabbitmq-ip` and `--rabbitmq-port`: RabbitMQ connection details.
- `--celery`: Run tasks with Celery workers.
- `--celery-worker-concurrency`: Number of worker threads for Celery.
- `--celery-worker-prefetch-count`: Prefetch count for Celery workers.

---

### Command Details

#### 1. `launchpad`
**Description**: Prepares and enqueues prompts for processing.

**Usage**:
```bash
promptlab launchpad \
    --tokenizer-path <path> \
    --templates-path <path> \
    --batch-size <size> \
    --orbiter-queue-name <queue-name> \
    --orbiter-task-name <task-name>
```

**Example**:
```bash
promptlab launchpad \
    --tokenizer-path tokenizer.json \
    --templates-path ./templates/ \
    --batch-size 32 \
    --orbiter-queue-name prompts_process_queue \
    --orbiter-task-name prompt_lab.celery_app.tasks.orbiter
```

---

#### 2. `orbiter`
**Description**: Queries the LLM with prepared prompts.

**Usage**:
```bash
promptlab orbiter \
    --model-name <model-name> \
    --model-api-url <api-url> \
    --reviewer-queue-name <queue-name> \
    --reviewer
```

**Example**:
```bash
promptlab orbiter \
    --model-name my-llm-model \
    --model-api-url http://127.0.0.1:8000/api \
    --reviewer-queue-name reviewed_queue \
    --reviewer
```

---

#### 3. `landing`
**Description**: Processes and manages the results of LLM queries.

**Usage**:
```bash
promptlab landing \
    --max-retry <number> \
    --reviewed-prompts-queue-name <queue-name> \
    --orbiter-queue-name <queue-name> \
    --output-dataset-repo <repo>
```

**Example**:
```bash
promptlab landing \
    --max-retry 5 \
    --reviewed-prompts-queue-name reviewed_queue \
    --orbiter-queue-name prompts_process_queue \
    --output-dataset-repo my-output-repo
```

---

### Docker Usage

To use the commands in Docker, prepend the `docker run` command:
```bash
docker run -it --rm promptlab-cli <command> [options]
```

**Example**:
```bash
docker run -it --rm promptlab-cli launchpad \
    --tokenizer-path tokenizer.json \
    --batch-size 32
```

---

## Configuration Details
The CLI reads its configuration from a JSON file. Environment variables are loaded into the config if they exist; otherwise, defaults are used. Override settings via CLI options for flexibility.

Example configuration:
```json
{
  "model_name": "example-model",
  "mongodb_ip": "127.0.0.1",
  "rabbitmq_ip": "127.0.0.1",
  "orbiter_queue_name": "prompts_queue"
}
```

To specify a custom config path, use:
```bash
promptlab --config-path ./config.json launchpad
```

---

This README should equip you with the knowledge to install, configure, and use PromptLab effectively. If you encounter any issues, feel free to reach out to the developer. Happy prompting! 😊

