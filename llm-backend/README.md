## Overview

This llm backend (BE) application is built with **Python** and based on the **Flask** framework. It serves as a backend for the GUI, providing several API endpoints that support the GUI’s functionality by managing data operations and handling requests.

## Key Features
("/api/backend/registerTrainedModel", methods=["POST"])
("/api/backend/loadModel", methods=["GET"])
("/api/backend/inference", methods=["GET"])
("/api/backend/stopInference", methods=["GET"])
("/api/backend/getModels", methods=["GET"])
("/api/backend/saveToken", methods=["POST"])
("/api/backend/getHfRepoFiles", methods=["GET"])
("/api/backend/getLoadedModel", methods=["GET"])
("/api/backend/unloadModel", methods=["GET"])
("/api/backend/clearChatHistory", methods=["GET"])
("/api/backend/loadChatContext", methods=["POST"])

## Data Storage

All application data, including dataset information and LLM prompt history, is stored in **MongoDB**. This ensures data persistence and efficient data retrieval to support GUI functionalities.

## Getting Started

### Prerequisites

podman installed.

### Installation

```bash
podman build --tag genie-llm-be.latest .
```

### Running the Application
```
podman run --name llm-be -e 'HF_TOKEN=hf_xxxxxx' -e 'VLLM_CONFIG_ROOT=/tmp/usage' -e 'HF_HOME=/tmp/' -e 'MONGODB_HOST=mongodb' -e 'BACKEND_ENV=production' genie-llm-be.latest
```
### API Documentation
Each API endpoint is documented with details on request methods, parameters, and example responses. Refer to the API documentation for a complete guide.

