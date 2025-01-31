## Overview

This backend (BE) application is built with **Python** and based on the **Flask** framework. It serves as a backend for the GUI, providing several API endpoints that support the GUI’s functionality by managing data operations and handling requests.

## Key Features

- **Dataset Management**: Endpoints in this section allow users to interact with dataset resources, such as:
  - **/files**: Lists all files within a specified Git repository.
  - **/forms**: Adds a new dataset form to the backend for future processing.

- **Inference Support**: Endpoints here support interactions with LLM models and provide options to:
  - Save selected model prompts and user interactions directly to the database.

## Data Storage

All application data, including dataset information and LLM prompt history, is stored in **MongoDB**. This ensures data persistence and efficient data retrieval to support GUI functionalities.

## Getting Started

### Prerequisites

podman installed.

### Installation

```bash
#cd the root. (Note: NOT the backend folder. The backend container build need include parallel folder `rag` so the podman build need be at the parent folder, ie root of the repo)
podman build --tag genie-backend.latest .
```

### Running the Application
```
podman run --name backend genie-backend.latest
```
### API Documentation
Each API endpoint is documented with details on request methods, parameters, and example responses. Refer to the API documentation for a complete guide.

