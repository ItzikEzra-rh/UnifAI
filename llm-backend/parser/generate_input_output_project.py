import json
import random
import requests
import re
import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-instruct-v0.3-bnb-4bit")

contextual_options = [
    """Project Description:
Red Hat OpenShift AI Overview
Red Hat OpenShift AI is a comprehensive platform that provides an end-to-end solution for developing, training, deploying, and serving AI/ML models. It offers a variety of features and integrations to streamline workflows for data scientists, AI developers, and infrastructure teams. The platform is designed to handle all stages of the AI/ML lifecycle, including data preparation, training, validation, deployment, and inference.

Key Components and Features:

Distributed Workloads: The platform supports distributed machine learning workloads, enabling parallel processing across multiple nodes for large-scale data processing and model training. Using the CodeFlare framework, users can manage and monitor distributed jobs efficiently, allowing for faster training and evaluation of models.

Data Science Pipelines: Data science pipelines facilitate building complex workflows that incorporate data preprocessing, model training, evaluation, and deployment. The pipelines are portable and support version control, making it easier to reproduce experiments and manage different versions of models. Users can configure experiments, manage runs, and schedule recurring tasks to automate machine learning workflows.

IDE Integration: OpenShift AI offers seamless integration with popular data science IDEs like Jupyter and VS Code. Users can connect their IDEs to the platform, allowing them to interact with data, train models, and manage workflows within their familiar development environment. This integration enables code execution directly on the cluster, providing access to resources and accelerators.

Data Science Projects: Projects serve as the organizational unit for workbenches, notebooks, models, and pipelines. Users can create collaborative workspaces where they can share code, data, and models with team members. OpenShift AI supports a variety of workflows, including notebook-based development, training, deployment, and experimentation.

Data Management with S3-Compatible Object Store: OpenShift AI integrates with S3-compatible object storage, allowing users to work with large datasets efficiently. This integration provides a scalable and flexible solution for data storage, making it easy to manage datasets, training data, and model outputs.

Model Serving: OpenShift AI provides robust model serving capabilities through two platforms:

Single-Model Serving Platform: Ideal for deploying large models like large language models (LLMs). Each model is deployed on a dedicated server, leveraging the KServe component for efficient scaling, monitoring, and maintenance.
Multi-Model Serving Platform: Designed for small to medium-sized models, allowing multiple models to share resources on the same server using the ModelMesh component. This approach optimizes resource utilization and is suitable for environments with limited compute resources.
Managing Accelerators: The platform supports hardware accelerators (such as GPUs and TPUs) to speed up data science workflows. This feature is particularly beneficial for training complex models, offering significant performance improvements and reducing the time needed for model training and inference.

Resource and User Management: OpenShift AI allows administrators to manage cluster resources, ensuring that projects and workloads have access to the necessary compute and storage. Users can define quotas, allocate resources, and monitor usage. The platform also offers comprehensive user management, enabling administrators to assign roles, permissions, and access levels to different team members.

Upgrading, Installing, and Uninstalling: The platform supports seamless installation, upgrades, and uninstallation processes in both connected and disconnected environments. This flexibility allows organizations to manage deployments in various network configurations, ensuring the platform remains up-to-date with minimal downtime.

Release Notes and Updates: OpenShift AI regularly releases updates that include new features, enhancements, bug fixes, and known issues, ensuring that users have access to the latest capabilities and improvements.

ODS-CI  Overview
ODS-CI is an open-source test automation framework specifically designed to validate and test OpenShift AI and Open Data Hub deployments. It ensures that the OpenShift AI platform and its components function correctly and reliably by providing automated testing capabilities.

Key Features and Details:

Test Automation: ODS-CI is built on the Robot Framework, which is widely used for test automation. It allows users to write automated test cases for various components of the OpenShift AI platform, covering end-to-end workflows, from data ingestion and preprocessing to model training, deployment, and inferencing. These tests ensure that all components work seamlessly together and adhere to expected behavior.

Integration with CI/CD Pipelines: ODS-CI integrates with continuous integration and continuous delivery (CI/CD) tools like Jenkins. This integration allows for automated testing of OpenShift AI deployments as part of the software development lifecycle. Every change to the platform or the models can be tested, validated, and deployed automatically, ensuring that issues are identified and resolved early in the process.

Multi-environment Support: The ODS-CI framework supports testing across various environments, whether on local machines, cloud infrastructure, or cluster-based deployments. This flexibility ensures that tests can be executed in diverse configurations, mirroring real-world deployment scenarios.

Selenium Integration: For testing web-based interfaces and dashboards, ODS-CI integrates with Selenium. This integration enables the automation of browser-based testing, allowing testers to interact with the OpenShift AI user interface and validate the functionality of web components.

Customizable Configurations: ODS-CI allows testers to define test variables, data sets, and configurations to suit different testing scenarios. Users can tailor their testing environment, making it possible to test specific use cases, workflows, or system configurations.

Test Suite and Virtual Environment Management: The framework supports the creation of comprehensive test suites that group related test cases, making it easier to manage and execute tests. It also allows the use of virtual environments to isolate dependencies and ensure consistent test execution.


Red Hat OpenShift AI, combined with ODS-CI, provides a comprehensive, enterprise-grade solution for developing, deploying, and testing AI/ML projects. OpenShift AI offers robust capabilities for handling large-scale machine learning workflows, while ODS-CI ensures that these workflows, models, and integrations are thoroughly validated through automated testing. This combination results in a reliable, scalable, and production-ready AI/ML environment that meets the demands of data scientists, AI developers, and infrastructure teams.
  
  
Location: `{file_location}`.

{class_code}

Code: {code}

Dependencies: {dependencies}.

Calls: {calls}.

Decorators: {decorators_text}.
 
 Please use this context to help with the answer.
"""
]

# Code as Input Options (Generic for Classes, Methods, Functions)
code_input_options = [
    "{element_type} `{name}`{class_text} is part of the ODS-CI test framework project, located at `{file_location}`. It relies on the following dependencies: {dependencies}. Describe its functionality:\n\n{code}",
    "Explain the purpose and functionality of the {element_type} `{name}`{class_text} from the ODS-CI test framework project, which is located at `{file_location}`. It uses the following calls: {calls}{decorators_text}. Code:\n\n{code}",
    "Analyze the {element_type} `{name}`{class_text} in the ODS-CI test framework project (file: {file_location}). This element depends on {dependencies} and uses the following calls: {calls}. Provide a detailed explanation of its purpose. Here's the code:\n\n{code}",
    "What is the core purpose of the {element_type} `{name}`{class_text}, found at `{file_location}` in the ODS-CI test framework project? Describe its role and functionality, focusing on how it uses {dependencies} and {calls}. Provide the code:\n\n{code}",
    "Within the ODS-CI test framework project, the {element_type} `{name}`{class_text}, located at `{file_location}`, is critical for handling {dependencies}. Use the following code to explain its purpose:\n\n{code}",
    "Describe the design of the {element_type} `{name}`{class_text} within the ODS-CI test framework project, as found at `{file_location}`. Include an explanation of {dependencies}, {calls}, and decorators: {decorators_text}. Code:\n\n{code}",
    "How does the {element_type} `{name}`{class_text} (file location: `{file_location}`) integrate within the ODS-CI test framework project? Show the code and describe how it interacts with {dependencies} and {calls}:\n\n{code}",
    "The {element_type} `{name}`{class_text}, found at `{file_location}` in the ODS-CI test framework project, is dependent on {dependencies}. Describe how it utilizes {calls} and {decorators_text}. Here’s the code:\n\n{code}",
    "Provide an analysis of the {element_type} `{name}`{class_text}, located at `{file_location}` in the ODS-CI test framework project. Explain its purpose and the code involved. It uses the following dependencies: {dependencies}, calls: {calls}, decorators: {decorators_text}:\n\n{code}",
    "In the ODS-CI test framework project, the {element_type} `{name}`{class_text} (file: `{file_location}`) is crucial. Describe its function and dependencies ({dependencies}), along with how it uses {calls} and {decorators_text}. Include the code:\n\n{code}"
]

human_input_options = [
    "What is the purpose of the {element_type} `{name}`{class_text}, located at `{file_location}` in the ODS-CI test framework project?",
    "Explain the role of the {element_type} `{name}`{class_text} in the ODS-CI test framework project and how it interacts with other parts of the project (file: `{file_location}`).",
    "How does the {element_type} `{name}`{class_text} from the ODS-CI (Open Data Science CI) test framework project function? Provide a high-level explanation.",
    "Why is the {element_type} `{name}`{class_text}, found at `{file_location}`, critical to the ODS-CI test framework project’s functionality? Provide a detailed explanation.",
    "Can you explain the main responsibilities of the {element_type} `{name}`{class_text}, located at `{file_location}` in the ODS-CI test framework project, and how it utilizes its dependencies?",
    "What are the primary functions of the {element_type} `{name}`{class_text}, located at `{file_location}`, and how do its {calls} and {dependencies} affect the ODS-CI test framework project?",
    "Explain how the {element_type} `{name}`{class_text}, found at `{file_location}`, works within the ODS-CI test framework project and how it handles dependencies like {dependencies}.",
    "What is the function of {element_type} `{name}`{class_text} in the ODS-CI test framework project, and how is it connected to other parts of the project? The file is located at `{file_location}`.",
    "Describe how the {element_type} `{name}`{class_text}, located at `{file_location}`, contributes to the ODS-CI test framework project. What role does it play, and how does it utilize {calls} and {dependencies}?",
    "In what way does the {element_type} `{name}`{class_text} (file: `{file_location}`) serve the ODS-CI test framework project, and how does it interact with its dependencies?"
]

code_snippet_input_options = [
    "Given the {element_type} `{name}`{class_text} located at `{file_location}` in the ODS-CI test framework project, provide both a description and example code for its functionality, including calls: {calls}{decorators_text}.",
    "For the {element_type} `{name}`{class_text} in the ODS-CI test framework project at {file_location}, summarize its purpose, list the methods it uses (calls: {calls}), {decorators_text}. Include the code.",
    "In the ODS-CI test framework project, combine a high-level overview of the {element_type} `{name}`{class_text} (file: {file_location}) with code snippets and explanations. Include dependencies: {dependencies}{decorators_text}, and the code.",
    "Describe the role of the {element_type} `{name}`{class_text}, located at {file_location} in the ODS-CI test framework project. Provide an example of its implementation with code, focusing on the calls: {calls} and {decorators_text}.",
    "Summarize the purpose of the {element_type} `{name}`{class_text}, found at {file_location} in the ODS-CI test framework project, and include code snippets demonstrating how it interacts with its dependencies: {dependencies} and calls: {calls}.",
    "How does the {element_type} `{name}`{class_text} work in the ODS-CI test framework project? It's located at {file_location}, and uses {calls}. Include an explanation and code snippet showcasing its functionality.",
    "In the ODS-CI test framework project, the {element_type} `{name}`{class_text} is crucial for {dependencies}. Describe its purpose, using {calls} and provide example code located at {file_location}.",
    "Describe the functionality of {element_type} `{name}`{class_text} within the ODS-CI test framework project, located at {file_location}. Provide a code example and explain how it uses its dependencies and methods, including {calls}.",
    "Show an example of the {element_type} `{name}`{class_text} located at {file_location} in the ODS-CI test framework project. Explain how it uses its dependencies ({dependencies}), calls ({calls}), and decorators: {decorators_text}, and include the code.",
    "Provide an overview of the {element_type} `{name}`{class_text}, which is part of the ODS-CI test framework project and located at {file_location}. Explain its purpose and use case with example code, focusing on its {dependencies}, {calls}, and {decorators_text}."
]



def generate_random_input(template_options, decorators, **kwargs):
    """Generate a randomized input string from template options."""
    # Conditionally include decorators text
    if decorators:
        kwargs["decorators_text"] = f" and has the following decorators: {decorators}"
    else:
        kwargs["decorators_text"] = ""

    if kwargs["element_type"] == "method":
        kwargs["class_text"] = f" exist in class `{kwargs['class_name']}`" if kwargs['class_name'] else ""
        kwargs["class_code"] = f" Class Code: `{kwargs['method_class_code']}`" if kwargs['method_class_code'] else ""
    else:
        kwargs["class_text"] = ""
        kwargs["class_code"] = ""

    template = random.choice(template_options)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template.format_map({key: kwargs.get(key, 'None') for key in kwargs})


def extract_assistant_text(text):
    # Try to extract text between <assistant> and </assistant>
    matches = re.findall(r'<assistant>(.*?)</assistant>', text, re.DOTALL)

    # If no match, fall back to extracting between <assistant> and </s>
    if not matches:
        matches = re.findall(r'<assistant>(.*?)</s>', text, re.DOTALL)

    return ' '.join(matches).strip()


def ask_llm(prompt):
    """Send a request to the LLM API to generate prompts based on the provided documentation and code."""
    response = requests.post(
        "http://127.0.0.1:443/api/backend/inference",
        json={"prompt": prompt, "contextLength": "2048"},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    res = extract_assistant_text(response.text)
    print(res)
    print()
    print('*****************************************************************')
    print()
    return res


def is_more_than_ctx(elem):
    inputs = tokenizer([elem], return_tensors="pt").to("cuda")
    token_ids = inputs['input_ids']

    # Calculate the number of tokens
    num_tokens = token_ids.size(1)

    # Filter elements based on the token count
    print(f"Number of tokens: {num_tokens}")
    if num_tokens > 32000:
        print(f"input number of tokens is bigger than 32768, skipping")
        return True
    return False


def process_element(element_data, element_type="element"):
    """Process a class, method, or function element by generating different types of inputs and corresponding outputs."""
    dataset = []
    name = element_data.get("class_name", "Unnamed") if element_type == "class" else element_data.get("function_name",
                                                                                                      "Unnamed")
    class_name = element_data.get("class_name", None)
    code = element_data.get("code", "")
    file_location = element_data.get("file_location", "Unknown")
    dependencies = element_data.get("dependencies", {}).get("imports", [])
    calls = element_data.get("calls", [])
    decorators = [decorator.get("decorator_function", "") for decorator in element_data.get("decorators", [])]
    method_class_code = element_data.get("method_class_code", None)

    context = generate_random_input(
        contextual_options,
        element_type=element_type,
        name=name,
        class_name=class_name,
        code=code,
        file_location=file_location,
        dependencies=', '.join(dependencies) if dependencies else 'None',
        calls=', '.join(calls) if calls else 'None',
        decorators=', '.join(decorators) if decorators else '',
        method_class_code=method_class_code
    )

    # (1) Code as Input (with dependencies, file location, calls, decorators)
    code_based_input = generate_random_input(
        code_input_options,
        element_type=element_type,
        name=name,
        class_name=class_name,
        code=code,
        file_location=file_location,
        dependencies=', '.join(dependencies) if dependencies else 'None',
        calls=', '.join(calls) if calls else 'None',
        decorators=', '.join(decorators) if decorators else '',
        method_class_code=method_class_code
    )

    prompt = f"<context>{context}</context><user>{code_based_input}</user><assistant>"
    if not is_more_than_ctx(prompt):
        code_based_output = {
            "code": code,
            "description": ask_llm(prompt),
            "dependencies": dependencies,
            "calls": calls,
            "decorators": decorators,
            "file_location": file_location
        }
        dataset.append({"input": code_based_input, "output": code_based_output, "type": "code_based_output"})

    # (2) Human-Level Input
    human_input = generate_random_input(human_input_options,
                                        element_type=element_type,
                                        name=name,
                                        class_name=class_name,
                                        code=code,
                                        file_location=file_location,
                                        dependencies=', '.join(dependencies) if dependencies else 'None',
                                        calls=', '.join(calls) if calls else 'None',
                                        decorators=', '.join(decorators) if decorators else '',
                                        method_class_code=method_class_code
                                        )

    prompt = f"<context>{context}</context><user>{human_input}</user><assistant>"
    if not is_more_than_ctx(prompt):
        human_output = {
            "code": code,
            "description": ask_llm(prompt),
            "dependencies": dependencies,
            "calls": calls,
            "decorators": decorators,
            "file_location": file_location
        }
        dataset.append({"input": human_input, "output": human_output, "type": "human_output"})

    # (3) Hybrid Input (with additional context)
    code_snippet_input = generate_random_input(
        code_snippet_input_options,
        element_type=element_type,
        name=name,
        class_name=class_name,
        code=code,
        file_location=file_location,
        dependencies=', '.join(dependencies) if dependencies else 'None',
        calls=', '.join(calls) if calls else 'None',
        decorators=', '.join(decorators) if decorators else '',
        method_class_code=method_class_code
    )

    prompt = f"<context>{context}</context><user>{code_snippet_input}</user><assistant>"
    if not is_more_than_ctx(prompt):
        code_snippet_output = {
            "code": code,
            "description": ask_llm(prompt),
            "dependencies": dependencies,
            "calls": calls,
            "decorators": decorators,
            "file_location": file_location
        }
        dataset.append({"input": code_snippet_input, "output": code_snippet_output, "type": "code_snippet_input"})

    return dataset


def process_class_methods(class_data):
    """Process methods inside a class."""
    dataset = []
    methods = class_data.get("methods", [])
    for method_data in methods:
        method_data['method_class_code'] = class_data.get("code", "")
        dataset.extend(process_element(method_data, element_type="method"))
    return dataset


def save_progress(current_index, full_dataset, progress_file):
    """Save the current dataset incrementally and track the current index."""
    with open(progress_file, 'w') as f:
        json.dump({"current_index": current_index}, f, indent=4)

    with open(output_file, 'w') as f:
        json.dump(full_dataset, f, indent=4)


def load_progress(output_file, progress_file):
    """Load the existing dataset and the current progress (last processed index)."""
    dataset = []
    current_index = 0
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            dataset = json.load(f)

    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
            current_index = progress_data.get("current_index", 0)

    return dataset, current_index


def process_json(json_data, output_file, progress_file):
    """Process the entire JSON dataset, extracting classes, methods, and functions."""
    full_dataset, current_index = load_progress(output_file, progress_file)

    total_classes = len(json_data.get("classes", []))
    total_functions = len(json_data.get("functions", []))

    total_elements = total_classes + total_functions

    # Process Classes and their Methods
    for idx, class_data in enumerate(json_data.get("classes", []), start=1):
        print(f"************************** {idx}/{total_elements} ***************************************")
        if idx < current_index:  # Skip elements already processed
            continue

        # Process the class itself
        full_dataset.extend(process_element(class_data, element_type="class"))

        # Process each method inside the class
        full_dataset.extend(process_class_methods(class_data))

        # Update current index and save progress after each class
        current_index = idx
        save_progress(current_index, full_dataset, progress_file)

    # Process Functions next
    for idx, function_data in enumerate(json_data.get("functions", []), start=total_classes + 1):
        print(f"************************** {idx}/{total_elements} ***************************************")
        if idx < current_index:  # Skip elements already processed
            continue

        # Process the function
        full_dataset.extend(process_element(function_data, element_type="function"))

        # Update current index and save progress after each function
        current_index = idx
        save_progress(current_index, full_dataset, progress_file)

    return full_dataset


# File paths
json_file_path = r"/home/instruct/AI-TC-s-Generator/llm-backend/parser/ods-ci_output_project_analysis.json"
output_file = r"/home/instruct/AI-TC-s-Generator/llm-backend/parser/ods-ci_py_processed_dataset.json"
progress_file = r"/home/instruct/AI-TC-s-Generator/llm-backend/parser/progress.json"

# Load JSON data
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Process the JSON and save the dataset
process_json(json_data, output_file, progress_file)
