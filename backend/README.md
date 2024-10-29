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

- Python 3.8 or above
- Flask
- MongoDB

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
    pip install -r requirementsBE.txt

### Running the Application
To start the Flask application, run:

bash
python app.py
This will start the server, making it available to handle requests from the GUI.

### API Documentation
Each API endpoint is documented with details on request methods, parameters, and example responses. Refer to the API documentation for a complete guide.

### Learn More
To learn more about Flask, visit the [Flask documentation](https://flask.palletsprojects.com/en/stable/).
For MongoDB, see the [MongoDB documentation](https://www.mongodb.com/docs/).
