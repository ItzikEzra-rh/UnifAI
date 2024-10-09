# AI-TC-s-Generator
The purpose of this project is to create a wrapper, comprising both a graphical user interface (GUI) and backend (BE) application, encapsulated within containers. 

This wrapper will facilitate an application that utilizes a pre-tuned Large Language Model (LLM) to generate test cases (TCs) for specific projects. 

The goal is to reduce the development time for automation teams by at least 70%. Users will input the content of TCs, and the LLM will generate relevant TCs adhering to the conventions of the user's project.

# How to start the LLM inference container (LLM engine  host/workshop VM)
## (optional ) stop  any service that using 443 port (eg in the workshop VM:  sudo service showroom stop)
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
podman build . -f Dockerfile.cuda --tag llm-be  .
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
Change the baseURL under ui/src/http/axiosLLMConfig.ts
Change the baseUrl under ui/src/components/ChatContainer.tsx - sendQuestion() METHOD - fetch(URL)
# How to start the UI in personal VM

```bash
cd ui
nvm use 16 # (you can use higher NVM version as well)
yarn install
yarn start
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
Change the baseURL under `ui/src/http/axiosLLMConfig.ts`
Change the baseUrl under `ui/src/components/ChatContainer.tsx - sendQuestion() METHOD - fetch(URL)`

