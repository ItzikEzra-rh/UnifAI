import json
import random
import requests
import re
import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-instruct-v0.3-bnb-4bit")

contextual_options = [
    """Project Description:
AIM (Application Infrastructure Monitoring) is a comprehensive monitoring tool designed to assist cloud users in debugging and analyzing issues related to Virtual Network Functions (VNFs) and Cloud-native Network Functions (CNFs) within cloud infrastructure environments. It is particularly tailored for OpenStack (CBIS) and Kubernetes (NCS) platforms.

Key Features:

Topology Visualization:

Displays both infrastructure resources (computes, controllers, nodes) and user resources (VMs, VNFs, Pods) in a graphical, intuitive interface.
Helps users understand the complex relationships and structures within the cloud environment.
Application Stats Collector (ASC):

The ASC is a core component of AIM that enables users to collect, visualize, and analyze real-time statistics from active VNFs and CNFs.
Samples:
Definition: A sample is a user-defined data collection session where specific metrics are gathered over a set duration.
Customization: Users can specify the sample name, target resources (stacks or VMs), and the duration of data collection.
Execution: Supports running, stopping, and re-running samples. Only one sample can be active at any given time.
Statistics Collected: Includes networking, storage, CPU, and memory utilization metrics.
Visualization: Live statistics can be displayed during the sample execution, offering immediate insights.
Reporting: Results can be downloaded in Excel or JSON formats for offline analysis or record-keeping.
Sample Statistics (NCS Only):
Provides detailed metrics at both the pod and container levels.
Metrics include CPU usage (millicores), memory usage (Mebibytes), throttled CPU percentage, and utilization percentages against requested and limit values.
Highlights resource utilization efficiency and potential bottlenecks.
Users can configure thresholds and view severity indicators based on utilization levels.
Non-Intrusive Monitoring:

Operates without impacting user resources by gathering data directly from underlying layers.
Agents are deployed on infrastructure nodes (computes, workers, edges) to collect data from the operating system and virtualization components.
Network Validation and Connectivity Checks:

Network Topology:
Provides a detailed view of the network structure within compute nodes, including OVS-switch entities and interfaces.
Allows users to visualize how VMs and Pods are interconnected.
Network Validation:
Enables validation of VLAN configurations across different cluster groups.
Users can specify VLAN ranges, MTU sizes, and interfaces to ensure network configurations are correctly set up.
Generates detailed reports highlighting any discrepancies or issues.
Ping Connectivity Check:
Offers basic network connectivity tests between two selected nodes (VMs or Pods).
Displays shared networks and allows users to perform ping tests with customizable MTU sizes.
Visualizes the results to quickly identify connectivity problems.
Cluster Audit and API Usage (NCS Only):

API Audit:
Logs the utilization of Kubernetes APIs across applications and pods.
Identifies deprecated APIs and those scheduled for removal in future Kubernetes releases.
Helps users proactively update their applications to maintain compatibility.
Cluster Audit:
Provides insights into the overall health and configuration of the cluster.
Command Ease (NCS Only):

Allows users to execute read-only commands on cluster nodes without requiring SSH access.
Simplifies troubleshooting by providing immediate access to command outputs through a guided interface.
Users select command categories, specific commands, target nodes, and parameters to retrieve the desired information.
Log Explorer (NCS Only):

Offers a tree-view navigation of directories and log files on cluster nodes.
Users can browse through the file system, locate specific log files, and download them directly for analysis.
Enhances the ability to troubleshoot issues without direct access to the nodes.
Tcpdump Integration:

Enables execution of tcpdump commands on selected nodes for packet capture.
Users can set time limits or file size restrictions to control the scope of the capture.
Captured data is streamed directly to the browser and can be downloaded in PCAP format for analysis with tools like Wireshark.
Provides options to specify interfaces, capture filters, and ensures that data does not persist on the cluster for security.
Deployment and Configuration:

Containerized Architecture:

AIM's UI and backend run as containers, ensuring a lightweight footprint and ease of deployment.
Agents are also containerized and deployed on infrastructure nodes.
Utilizes an Ansible-based installation script for straightforward setup and removal.
Customizable Ports and Network Requirements:

Default ports are specified for AIM components (e.g., UI on port 9990), but these can be customized during installation to avoid conflicts.
Requires certain network access permissions to function correctly, such as access to RabbitMQ and MongoDB ports.
Supported Platforms:

OpenStack (CBIS 19+):

AIM integrates with the Undercloud and compute nodes.
Agents connect via the underlay provisioning network, leveraging existing Ansible configurations.
Kubernetes (NCS 20+):

AIM runs on master/controller nodes, with agents on worker and edge nodes.
Connects using the same network and credentials as kubectl.
Supports additional features exclusive to NCS, such as Sample Statistics, Cluster Audit, Command Ease, and Log Explorer.
Usage Scenarios:

Debugging and Issue Resolution:

Provides support teams with tools to quickly diagnose and resolve infrastructure-related issues.
Reduces downtime by offering precise and comprehensive data.
Performance Monitoring:

Allows users to monitor resource utilization over time, helping to identify bottlenecks or inefficient resource usage.
The ASC and sampling features enable proactive performance tuning.
Infrastructure Overview and Compliance:

Offers a holistic view of the cloud environment, aiding in understanding complex setups.
Ensures network configurations and API usages are up-to-date and compliant with future platform versions.
Additional Notes:

Ease of Use:

AIM is designed to be intuitive, with a graphical interface and straightforward workflows.
Installation and uninstallation are simplified through provided scripts.
Non-Intrusiveness:

The tool is designed to have a minimal footprint and does not interfere with user workloads.
Data collection is performed in a way that does not impact the performance of VNFs or CNFs.

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
    "{element_type} `{name}`{class_text} is part of the AIM tool, located at `{file_location}`. It relies on the following dependencies: {dependencies}. Describe its functionality:\n\n{code}",
    "Explain the purpose and functionality of the {element_type} `{name}`{class_text} from the AIM (Application Infrastructure Monitoring) tool, which is located at `{file_location}`. It uses the following calls: {calls}{decorators_text}. Code:\n\n{code}",
    "Analyze the {element_type} `{name}`{class_text} in the AIM (Application Infrastructure Monitoring) Cloudband project (file: {file_location}). This element depends on {dependencies} and uses the following calls: {calls}. Provide a detailed explanation of its purpose. Here's the code:\n\n{code}",
    "What is the core purpose of the {element_type} `{name}`{class_text}, found at `{file_location}` in the AIM tool? Describe its role and functionality, focusing on how it uses {dependencies} and {calls}. Provide the code:\n\n{code}",
    "Within the AIM project, the {element_type} `{name}`{class_text}, located at `{file_location}`, is critical for handling {dependencies}. Use the following code to explain its purpose:\n\n{code}",
    "Describe the design of the {element_type} `{name}`{class_text} within the AIM tool, as found at `{file_location}`. Include an explanation of {dependencies}, {calls}, and decorators: {decorators_text}. Code:\n\n{code}",
    "How does the {element_type} `{name}`{class_text} (file location: `{file_location}`) integrate within AIM? Show the code and describe how it interacts with {dependencies} and {calls}:\n\n{code}",
    "The {element_type} `{name}`{class_text}, found at `{file_location}` in AIM, is dependent on {dependencies}. Describe how it utilizes {calls} and {decorators_text}. Here’s the code:\n\n{code}",
    "Provide an analysis of the {element_type} `{name}`{class_text}, located at `{file_location}` in AIM. Explain its purpose and the code involved. It uses the following dependencies: {dependencies}, calls: {calls}, decorators: {decorators_text}:\n\n{code}",
    "In AIM, the {element_type} `{name}`{class_text} (file: `{file_location}`) is crucial. Describe its function and dependencies ({dependencies}), along with how it uses {calls} and {decorators_text}. Include the code:\n\n{code}"
]

human_input_options = [
    "What is the purpose of the {element_type} `{name}`{class_text}, located at `{file_location}` in the AIM project?",
    "Explain the role of the {element_type} `{name}`{class_text} in the AIM tool and how it interacts with other parts of the project (file: `{file_location}`).",
    "How does the {element_type} `{name}`{class_text} from Cloudband's AIM (Application Infrastructure Monitoring) tool function? Provide a high-level explanation.",
    "Why is the {element_type} `{name}`{class_text}, found at `{file_location}`, critical to the AIM project's functionality? Provide a detailed explanation.",
    "Can you explain the main responsibilities of the {element_type} `{name}`{class_text}, located at `{file_location}` in AIM, and how it utilizes its dependencies?",
    "What are the primary functions of the {element_type} `{name}`{class_text}, located at `{file_location}`, and how do its {calls} and {dependencies} affect the AIM project?",
    "Explain how the {element_type} `{name}`{class_text}, found at `{file_location}`, works within AIM and how it handles dependencies like {dependencies}.",
    "What is the function of {element_type} `{name}`{class_text} in AIM, and how is it connected to other parts of the project? The file is located at `{file_location}`.",
    "Describe how the {element_type} `{name}`{class_text}, located at `{file_location}`, contributes to AIM. What role does it play, and how does it utilize {calls} and {dependencies}?",
    "In what way does the {element_type} `{name}`{class_text} (file: `{file_location}`) serve the AIM project, and how does it interact with its dependencies?"
]

code_snippet_input_options = [
    "Given the {element_type} `{name}`{class_text} located at `{file_location}` in AIM (Application Infrastructure Monitoring), provide both a description and example code for its functionality, including calls: {calls}{decorators_text}.",
    "For the {element_type} `{name}`{class_text} in AIM (Application Infrastructure Monitoring) at {file_location}, summarize its purpose, list the methods it uses (calls: {calls}), {decorators_text}. Include the code.",
    "In AIM (Application Infrastructure Monitoring) project, combine a high-level overview of the {element_type} `{name}`{class_text} (file: {file_location}) with code snippets and explanations. Include dependencies: {dependencies}{decorators_text}, and the code.",
    "Describe the role of the {element_type} `{name}`{class_text}, located at {file_location} in AIM. Provide an example of its implementation with code, focusing on the calls: {calls} and {decorators_text}.",
    "Summarize the purpose of the {element_type} `{name}`{class_text}, found at {file_location} in the AIM project, and include code snippets demonstrating how it interacts with its dependencies: {dependencies} and calls: {calls}.",
    "How does the {element_type} `{name}`{class_text} work in AIM? It's located at {file_location}, and uses {calls}. Include an explanation and code snippet showcasing its functionality.",
    "In the AIM project, the {element_type} `{name}`{class_text} is crucial for {dependencies}. Describe its purpose, using {calls} and provide example code located at {file_location}.",
    "Describe the functionality of {element_type} `{name}`{class_text} within AIM, located at {file_location}. Provide a code example and explain how it uses its dependencies and methods, including {calls}.",
    "Show an example of the {element_type} `{name}`{class_text} located at {file_location} in AIM. Explain how it uses its dependencies ({dependencies}), calls ({calls}), and decorators: {decorators_text}, and include the code.",
    "Provide an overview of the {element_type} `{name}`{class_text}, which is part of the AIM tool and located at {file_location}. Explain its purpose and use case with example code, focusing on its {dependencies}, {calls}, and {decorators_text}."
]


def generate_random_input(template_options, decorators, **kwargs):
    """Generate a randomized input string from template options."""
    # Conditionally include decorators text
    if decorators:
        kwargs["decorators_text"] = f" and has the following decorators: {decorators}"
    else:
        kwargs["decorators_text"] = ""

    if kwargs["element_type"] == "method":
        kwargs["class_text"] = f" and exist in class `{kwargs['class_name']}`" if kwargs['class_name'] else ""
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
json_file_path = r"/home/instruct/testgenie/llm-backend/parser/output_project_analysis.json"
output_file = r"/home/instruct/testgenie/llm-backend/parser/processed_dataset.json"
progress_file = r"/home/instruct/testgenie/llm-backend/parser/progress.json"

# Load JSON data
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Process the JSON and save the dataset
process_json(json_data, output_file, progress_file)
