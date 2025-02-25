# AI-TC-Generator

The purpose of this project is to create a containerized application, including both a graphical user interface (GUI) and backend (BE), to streamline the generation of test cases (TCs) using a fine-tuned Large Language Model (LLM).

This wrapper application enables users to generate TCs specifically tailored to their projects and provides insightful project summaries, advanced analyses, and actionable recommendations.

The project’s goal is to reduce test development time for automation teams by at least 70%. Users will input TC content, and the LLM will generate relevant TCs that adhere to project-specific standards.

## Project Components

1) **Backend**  
   Serves as the backend for the GUI, offering multiple API endpoints that support GUI functionalities by managing data operations and handling requests.

2) **Data Pre-Processing**  
   Contains various parsers for multiple programming languages using Tree-sitter (an open-source library) to generate abstract syntax trees (ASTs).

3) **LLM Backend**  
   Hosts and serves fine-tuned LLM models.

4) **Prompt Lab**  
   A flexible tool for customizable prompt generation, enabling dynamic prompt creation and processing for project-specific needs.

5) **User Interface (UI)**  
   Provides an interactive platform for creating datasets, training models, and interacting with fine-tuned models.


# How to start the LLM inference container (LLM engine  host/workshop VM)
(optional ) stop  any service that using 443 port (eg in the workshop VM:  sudo service showroom stop)

## Configure the production repository and install nvidia container toolkit
Install the nvidia repo

```bash
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
```

Install the NVIDIA Container Toolkit packages:

```bash
sudo yum install -y nvidia-container-toolkit
```

## generate the cdi (Container Device Interface specifications) spec

```sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml```

## build the container image

```bash
cd llm-backend
podman build . -f Dockerfile --tag llm-be  .
```

## bring up the llm backedn and mongod

```bash
podman-compose -f compose.yaml up -d
```

# How to start the BE in personal VM

```bash
cd backend
virtualenv venv
```

(create new virtualenv)

```bash
pip install -r requirementsBE.txt
python app.py
```

# How to connect with LLM VM
Change the baseURL to where your LLM BE is server under the file: ``` ui/src/http/axiosLLMConfig.ts ```

# How to start the UI in personal VM

```bash
cd ui
nvm use 16 # (you can use higher NVM version as well)
yarn install
yarn start
```
