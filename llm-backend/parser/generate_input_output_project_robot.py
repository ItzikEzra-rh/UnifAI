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

The following metadata and code are from the ODS-CI project:  
  
file Location: `{file_location}`.

{file_code}

Here is the code for the {element_type}:\n\n{code}

{settings}

{imports_file_locations}

{variables}

{calls}
 
Please use this context to help with the answer.
"""
]

# full test:

# Full Test Functional Options
full_test_functional_options = 'full_test_functional_options', [
    "Provide a functional description of the robot test `{name}`, located at `{file_location}` in ODS-CI. How does it verify key functionalities through its test cases and associated keywords?",
    "Explain the core functionality of the robot test `{name}`, found at `{file_location}`. How do the test cases and keywords validate essential features in ODS-CI?",
    "Analyze the role of the robot test `{name}`, located at `{file_location}`. What critical paths do the test cases validate, and how are keywords used in this process?",
    "What is the functional purpose of the robot test `{name}`, located at `{file_location}`? How do the test cases and keywords contribute to the overall testing strategy in ODS-CI?",
    "Describe how the robot test `{name}`, located at `{file_location}`, ensures the validation of key features by leveraging specific test cases and keywords.",
    "Explain the key scenarios covered by the robot test `{name}`, located at `{file_location}`. How do its test cases and keywords verify core functionalities?",
    "What specific functionalities are tested by `{name}`, located at `{file_location}`? How do its test cases and keywords contribute to validating critical workflows?",
    "Analyze the validation steps in the robot test `{name}`, located at `{file_location}`. How do the test cases and keywords work together to ensure that the system functions as expected?",
    "How does the robot test `{name}`, located at `{file_location}`, provide comprehensive functional coverage in ODS-CI through its test cases and keywords?",
    "What is the role of the robot test `{name}`, located at `{file_location}`, in verifying functionalities within ODS-CI? How are test cases and keywords utilized for validation?"
]

# Full Test Workflow Options
full_test_workflow_options = 'full_test_workflow_options', [
    "Describe the end-to-end workflow of the robot test `{name}`, located at `{file_location}`. How do the test cases and keywords interact with other tests and resources in ODS-CI?",
    "Explain how the robot test `{name}`, located at `{file_location}`, executes its workflow. How are test cases and keywords organized to ensure smooth execution of scenarios?",
    "Analyze the workflow of `{name}`, located at `{file_location}`. How do the test cases and keywords collaborate with other elements in the ODS-CI project?",
    "What is the role of `{name}`, located at `{file_location}`, in orchestrating workflows across test scenarios? How do the test cases and keywords ensure coordination?",
    "Describe the execution flow of the robot test `{name}`, located at `{file_location}`. How are test cases and keywords structured to coordinate with other elements in the suite?",
    "Explain the workflow and execution sequence of `{name}`, located at `{file_location}`. How do test cases and keywords orchestrate the components of this test?",
    "How does `{name}`, located at `{file_location}`, manage multiple workflow paths in ODS-CI? Describe the role of test cases and keywords in handling dependencies.",
    "Analyze the flow of the robot test `{name}`, located at `{file_location}`. How do test cases and keywords ensure proper execution of interconnected scenarios?",
    "How does the robot test `{name}`, located at `{file_location}`, organize its dependencies and workflow paths using its test cases and keywords?",
    "What is the overall workflow of `{name}`, located at `{file_location}`? How do the test cases and keywords interact with other test cases?"
]

# Full Test Structural Options
full_test_structural_options = 'full_test_structural_options', [
    "Describe the structure and purpose of the robot test `{name}`, located at `{file_location}` in ODS-CI. How are test cases and keywords organized, and how do they relate to each other? Provide code snippets to illustrate.",
    "Explain the organization and structure of the robot test `{name}`, found at `{file_location}`. How do test cases integrate with keywords, and include relevant code examples.",
    "Analyze the structure of the robot test `{name}`, located at `{file_location}`. How do test cases utilize keywords for setup, execution, and teardown? Provide code snippets for clarity.",
    "What is the structure of the robot test `{name}`, located at `{file_location}`? How are test cases and keywords arranged to manage the sequence of actions? Include code examples to demonstrate this.",
    "Describe the key structural components and code of the robot test `{name}`, located at `{file_location}`. How do test cases and keywords interact to ensure logical flow? Provide snippets for illustration.",
    "Explain how the robot test `{name}`, located at `{file_location}`, organizes test cases and keywords for executing various scenarios. Include code examples to show these interactions.",
    "How does the robot test `{name}`, located at `{file_location}`, manage the structure of test cases and keywords? How are they connected, and what does the code look like? Provide code snippets.",
    "Analyze the structural flow and key code elements of `{name}`, located at `{file_location}`. How do test cases use keywords to organize steps and validations? Show relevant code snippets.",
    "How does the robot test `{name}`, located at `{file_location}`, organize test cases and keywords to ensure clarity and readability? Provide examples from the code.",
    "What is the overall structure of `{name}`, located at `{file_location}`? How do test cases and keywords work together to validate the scenarios? Include code examples to demonstrate this."
]


# Resource file:

# Full Resource Functional Options
full_resource_functional_options = 'full_resource_functional_options', [
    "Provide a detailed description of the resource file `{name}`, located at `{file_location}` in ODS-CI. What are the primary keywords, and how are they designed to provide shared functionality?",
    "Explain the functional role of the resource file `{name}`, located at `{file_location}`. How do its keywords support reusability across various tests?",
    "Analyze the purpose of the resource file `{name}`, located at `{file_location}` in ODS-CI. How are the keywords structured to enhance reusability?",
    "What is the functional purpose of the resource file `{name}`, located at `{file_location}`? How do the keywords within it enable shared functionalities?",
    "Describe how the resource file `{name}`, located at `{file_location}`, supports modularity through its keywords. How are these keywords used across different tests?",
    "Explain the key functionalities provided by the resource file `{name}`, located at `{file_location}`. How do the keywords contribute to test efficiency and modularity?",
    "What shared functionalities are provided by `{name}`, located at `{file_location}`? Focus on the design and relationships of its keywords.",
    "Analyze the reusable components in the resource file `{name}`, located at `{file_location}`. How do the keywords interact to centralize functionality?",
    "How does the resource file `{name}`, located at `{file_location}`, ensure functionality across ODS-CI tests through its keywords? Describe the keyword relationships.",
    "What role does the resource file `{name}`, located at `{file_location}`, play in test development? Focus on how its keywords facilitate modular development."
]

# Full Resource Structural Options
full_resource_structural_options = 'full_resource_structural_options', [
    "Describe the structure of the resource file `{name}`, located at `{file_location}` in ODS-CI. How are the keywords organized, and what are their relationships?",
    "Explain the structural design of the resource file `{name}`, located at `{file_location}`. How are keywords structured to support shared functionalities?",
    "Analyze the structure of the resource file `{name}`, located at `{file_location}` in ODS-CI. How do the keywords relate to each other and support reusability?",
    "What is the structure of the resource file `{name}`, located at `{file_location}`? Describe the organization of keywords and how they connect.",
    "Describe how the resource file `{name}`, located at `{file_location}`, organizes its keywords. How do these keywords interact to support the overall structure?",
    "Explain how the resource file `{name}`, located at `{file_location}`, structures its keywords for reusability and integration.",
    "How does the resource file `{name}`, located at `{file_location}`, organize its keywords? Describe their structure and relationships.",
    "Analyze the structure of `{name}`, located at `{file_location}`. How are keywords arranged to centralize reusable components?",
    "How does the resource file `{name}`, located at `{file_location}`, organize its keywords for modularity? What are the relationships between keywords?",
    "What is the structural design of `{name}`, located at `{file_location}`? Describe how its keywords are arranged to support the test suite."
]

# Full Resource Integration Options
full_resource_integration_options = 'full_resource_integration_options', [
    "Describe the purpose and main keywords in the resource file `{name}`, located at `{file_location}`. Provide code examples to illustrate its key components.",
    "Explain the role and functionality of the resource file `{name}`, located at `{file_location}`. How are its keywords structured? Include relevant code snippets.",
    "Analyze the primary keywords and their uses within the resource file `{name}`, found at `{file_location}`. Provide code examples to show how they function.",
    "What are the main components of the resource file `{name}`, located at `{file_location}`? Describe its keywords and provide code snippets to demonstrate their usage.",
    "Describe how `{name}`, located at `{file_location}`, is organized. Focus on the structure and purpose of its keywords, including relevant examples from the code.",
    "Explain the main keywords within `{name}`, located at `{file_location}`. How are they defined and used? Include code snippets for a clearer understanding.",
    "How does `{name}`, located at `{file_location}`, utilize keywords to support testing workflows? Provide examples from the code to illustrate.",
    "Analyze the structure and content of `{name}`, located at `{file_location}`. Describe its keywords and include code snippets to show how they are employed.",
    "What are the primary keywords in the resource file `{name}`, located at `{file_location}`? Provide code examples to demonstrate their setup and use.",
    "Describe the overall structure of `{name}`, located at `{file_location}`. How do its keywords support test cases? Include relevant code snippets."
]


# keyword / test case
# ---------------------

code_input_options = 'code_input_options', [
    "{element_type} `{name}` is located at `{file_location}` in the ODS-CI project. Describe its functionality, focusing on how it interacts with other keywords or test cases and implements the expected behavior:\n\n{code}",
    "Explain the purpose and functionality of `{element_type}` `{name}` in the ODS-CI project, located at `{file_location}`. How does this element contribute to executing a particular scenario or validating specific conditions?\n\n{code}",
    "Analyze the `{element_type}` `{name}`, found at `{file_location}`. Provide a detailed explanation of its purpose and how it works within the overall test suite to achieve comprehensive test coverage:\n\n{code}",
    "What is the core purpose of `{element_type}` `{name}`, located at `{file_location}`? Describe how this keyword or test case helps in verifying functionality or setup in the ODS-CI test suite:\n\n{code}",
    "`{element_type}` `{name}`, located at `{file_location}`, is crucial for handling specific tasks in the ODS-CI project. Use the following code to explain its purpose:\n\n{code}",
    "Describe the design of `{element_type}` `{name}`, found at `{file_location}`. How does the code ensure proper validation, setup, or teardown in the context of this test suite?\n\n{code}",
    "How does `{element_type}` `{name}`, located at `{file_location}`, integrate with other test cases or keywords in the ODS-CI project? Provide the code and describe how it enhances test automation:\n\n{code}",
    "Provide an analysis of the `{element_type}` `{name}` in the ODS-CI project, located at `{file_location}`. Explain how this keyword or test case is used to automate specific workflows or processes:\n\n{code}",
    "In the ODS-CI project, `{element_type}` `{name}`, located at `{file_location}`, plays a critical role in executing certain test cases. Include the code and explain its function:\n\n{code}",
    "For `{element_type}` `{name}`, located at `{file_location}`, explain how it interacts with the test suite. Provide the code and explain its purpose:\n\n{code}"
]

human_input_options = 'human_input_options', [
    "What is the purpose of `{element_type}` `{name}`, located at `{file_location}` in the ODS-CI project? How does it contribute to overall test automation?",
    "Explain the role of `{element_type}` `{name}`, located at `{file_location}` in the test suite. How does it help automate the validation or setup of specific scenarios?",
    "How does `{element_type}` `{name}`, found at `{file_location}`, function in the ODS-CI project? Describe its importance in the test case execution.",
    "Why is `{element_type}` `{name}`, located at `{file_location}`, critical to the ODS-CI test project? Explain how it fits into the test flow.",
    "Can you explain the main responsibilities of `{element_type}` `{name}`, located at `{file_location}`? How does it enhance the testing process?",
    "What are the primary functions of `{element_type}` `{name}`, located at `{file_location}`? How does it support test case execution or validation?",
    "Explain how `{element_type}` `{name}`, located at `{file_location}`, works within the ODS-CI project. How does it automate key steps in the process?",
    "What is the function of `{element_type}` `{name}`, located at `{file_location}` in the ODS-CI project? How does it help achieve test objectives?",
    "Describe how `{element_type}` `{name}`, located at `{file_location}`, contributes to test automation. How does it interact with other resources or test cases?",
    "How does `{element_type}` `{name}`, located at `{file_location}`, serve the ODS-CI project? How does it integrate with other test elements?"
]

code_snippet_input_options = 'code_snippet_input_options', [
    "For `{element_type}` `{name}`, located at `{file_location}`, provide both a description and example code. Explain how it helps automate specific tasks in the test suite:\n\n{code}",
    "Summarize the purpose of `{element_type}` `{name}`, located at `{file_location}`. Provide the code and explain how it contributes to validating specific test scenarios:\n\n{code}",
    "In the ODS-CI project, `{element_type}` `{name}` is located at `{file_location}`. Combine an overview with code snippets to explain its purpose in automating test processes:\n\n{code}",
    "Describe the role of `{element_type}` `{name}`, located at `{file_location}`, in the ODS-CI project. Provide the code and explain how it executes validation or setup steps:\n\n{code}",
    "How does `{element_type}` `{name}`, located at `{file_location}`, function in the project? Provide the code and explain how it automates testing tasks:\n\n{code}",
    "In the ODS-CI project, `{element_type}` `{name}` is crucial for running specific test cases. Provide a code example and explain how it works:\n\n{code}",
    "Describe the design of `{element_type}` `{name}`, located at `{file_location}`. Provide code snippets and explain its role in automating tasks:\n\n{code}",
    "Show an example of `{element_type}` `{name}`, located at `{file_location}`, in the ODS-CI project. Provide the code and describe how it integrates into the suite:\n\n{code}",
    "Provide an overview of `{element_type}` `{name}`, located at `{file_location}`, in the ODS-CI project. Include the code and explain its role:\n\n{code}",
    "Explain the functionality of `{element_type}` `{name}`, located at `{file_location}`. Provide a code example and describe its purpose:\n\n{code}"
]

structural_prompt = 'structural_prompt', [
    "Write a prompt that could be used to instruct the LLM to generate a Robot Test for {name}, in ODS-CI. The prompt should outline a sequence of steps for a test that includes specific actions and keywords. Reference the following test code to craft your response:\n\n{code}\n\nThe prompt should guide the LLM to produce the same test code by following these steps."]
free_text_prompt = 'free_text_prompt', [
    "Create a prompt that would allow a user to instruct the LLM to generate the Robot Test {name}. The prompt should describe the test's purpose, key functionalities, and dependencies. Use the following code as inspiration:\n\n{code}\n\nThe goal is to have the LLM output the exact test code based on a rich descriptive prompt."]
free_text_prompt_creative = 'free_text_prompt_creative', [
    "Craft a creative prompt that could be given to the LLM to generate the Robot Test {name} in ODS-CI. The prompt should provide a high-level overview of the test's role, objectives, and interactions, without going into step-by-step details. Use the following code to inform your response:\n\n{code}\n\nThe intent is for the LLM to generate the full test code from this creative summary prompt."]
prompts = [structural_prompt, free_text_prompt, free_text_prompt_creative]

test_input_options = [full_test_functional_options,
                      full_test_workflow_options,
                      full_test_structural_options]
test_input_options.extend(prompts)
resource_input_options = [full_resource_functional_options,
                          full_resource_structural_options,
                          full_resource_integration_options]
keyword_test_cases_input_options = [code_input_options,
                                    human_input_options,
                                    code_snippet_input_options]


def generate_random_input(template_options, **kwargs):
    """Generate a randomized input string from template options."""
    if kwargs["element_type"] == "Resource" or kwargs["element_type"] == "Test":
        kwargs["name"] = os.path.basename(kwargs['file_location'])

    if kwargs["file_code"] and (kwargs["element_type"] == "Keyword" or kwargs["element_type"] == "Test_Case"):
        kwargs[
            "file_code"] = f'The following code belongs to the file where the {kwargs["element_type"]} {kwargs["name"]} is defined:\n\n{kwargs["file_code"]}'
    else:
        kwargs["file_code"] = ""

    if kwargs["settings"]:
        kwargs[
            "settings"] = f'The following settings are used by the {kwargs["element_type"]} "{kwargs["name"]}":\n\n{kwargs["settings"]}'
    else:
        kwargs["settings"] = ""

    if kwargs["variables"]:
        kwargs[
            "variables"] = f'The following variables are used by the {kwargs["element_type"]} "{kwargs["name"]}":\n\n{kwargs["variables"]}'
    else:
        kwargs["variables"] = ""

    if kwargs["calls"]:
        keywords = ""
        for keyword, details in kwargs["calls"].items():
            keywords += f'- Keyword: "{keyword}"\n  Found in resource file: {details["file_location"]}\n\n'
        kwargs["calls"] = f'The {kwargs["element_type"]} "{kwargs["name"]}" uses the following keywords:\n\n{keywords}'
    else:
        kwargs["calls"] = ""

    if kwargs["imports_file_locations"]:
        imports_file_locations = ""
        for resource, path in kwargs["imports_file_locations"].items():
            imports_file_locations += (
                f'The {kwargs["element_type"]} "{kwargs["name"]}" imports the resource "{resource}", '
                f'located at: {path}\n'
            )
        kwargs["imports_file_locations"] = imports_file_locations
    else:
        kwargs["imports_file_locations"] = ''

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
        json={"prompt": prompt, "contextLength": "8192"},
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
    if num_tokens > 8192:
        print(f"input number of tokens is bigger than 32768, skipping")
        return True
    return False


def process_element(element_data, file_element):
    """Process a Keyword, Resource, Test_Case, or Test element."""
    dataset = []
    file_code = file_element.get("code", "")
    element_type = element_data.get("type")
    name = element_data.get("additional_data", {}).get("name", None)
    code = element_data.get("code", "")
    file_location = element_data.get("file_location", "")
    settings = element_data.get("dependencies", {}).get("settings", "")
    variables = element_data.get("dependencies", {}).get("variables", "")
    calls = element_data.get("calls", [])
    imports_file_locations = element_data.get("imports_file_locations", {})

    # Select templates based on element type
    if element_type == "Keyword":
        input_options = keyword_test_cases_input_options
    elif element_type == "Resource":
        input_options = resource_input_options
    elif element_type == "Test_Case":
        input_options = keyword_test_cases_input_options
    elif element_type == "Test":
        input_options = test_input_options
    else:
        return dataset

    # Generate context
    context = generate_random_input(
        contextual_options,
        element_type=element_type,
        file_code=file_code,
        name=name,
        code=code,
        file_location=file_location,
        settings=settings,
        variables=variables,
        imports_file_locations=imports_file_locations,
        calls=calls
    )

    # Generate inputs and outputs
    for input_type, input_template in input_options:
        input_text = generate_random_input(
            input_template,
            element_type=element_type,
            file_code=file_code,
            name=name,
            code=code,
            file_location=file_location,
            settings=settings,
            variables=variables,
            imports_file_locations=imports_file_locations,
            calls=calls
        )

        prompt = f"<context>{context}</context><user>{input_text}</user><assistant>"
        if not is_more_than_ctx(prompt):
            output = {
                "code": code,
                "description": ask_llm(prompt),
                "settings": settings,
                "calls": calls,
                "file_location": file_location,
                "imports_file_locations": imports_file_locations,
                "variables": variables,
                "name": name

            }
            dataset.append(
                {"input": input_text, "output": output, "element_type": element_type, 'input_type': input_type})

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

    total_elements = len(json_data)

    # Process Classes and their Methods
    for idx, file_data in enumerate(json_data, start=1):
        print(f"************************** {idx}/{total_elements} ***************************************")
        if idx < current_index:  # Skip elements already processed
            continue
        file_element = file_data[0]
        for element in file_data:
            # Process the file and its elements itself
            full_dataset.extend(process_element(element, file_element))

        current_index = idx
        save_progress(current_index, full_dataset, progress_file)

    return full_dataset


# File paths
json_file_path = r"/home/instruct/testgenie/llm-backend/parser/RHOAI_Files_Mapping.json"
output_file = r"/home/instruct/testgenie/llm-backend/parser/RHOI_processed_dataset.json"
progress_file = r"/home/instruct/testgenie/llm-backend/parser/progress.json"

# Load JSON data
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Process the JSON and save the dataset
process_json(json_data, output_file, progress_file)
