# AI-TC-s-Generator
The purpose of this project is to create a wrapper, comprising both a graphical user interface (GUI) and backend (BE) application, encapsulated within containers. This wrapper will facilitate an application that utilizes a pre-tuned Large Language Model (LLM) to generate test cases (TCs) for specific projects. The goal is to reduce the development time for automation teams by at least 70%. Users will input the content of TCs, and the LLM will generate relevant TCs adhering to the conventions of the user's project.

# How to start the UI in personal VM
cd ui
nvm use 16 (you can use higher NVM version as well)
yarn install
yarn start

# How to start the BE in personal VM
cd backend
virtualenv venv (create new virtualenv)
pip install -r requirementsBE.txt
python app.py

# How to connect with LLM VM
Change the baseURL under ui/src/http/axiosLLMConfig.ts
Change the baseUrl under ui/src/components/ChatContainer.tsx - sendQuestion() METHOD - fetch(URL)