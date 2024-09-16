import json
import random
import requests
import re
import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-instruct-v0.3-bnb-4bit")

# Code as Input Options (Generic for Classes, Methods, Functions)
code_input_options = [
    "{element_type} `{name}` is part of the AIM tool in Cloudband, located at `{file_location}`. It relies on the following dependencies: {dependencies}. Describe its functionality:\n\n{code}",
    "Explain the purpose and functionality of the {element_type} `{name}` from the AIM tool in Cloudband, which is located at `{file_location}`. It uses the following calls: {calls}{decorators_text}. Code:\n\n{code}",
    "Analyze the {element_type} `{name}` in the AIM Cloudband project (file: {file_location}). This element depends on {dependencies} and uses the following calls: {calls}. Provide a detailed explanation of its purpose. Here's the code:\n\n{code}"
]

human_input_options = [
    "What is the purpose of the {element_type} `{name}` located at `{file_location}` in the AIM project?",
    "Explain the role of the {element_type} `{name}` in the AIM tool and how it interacts with other parts of the project (file: {file_location}).",
    "How does the {element_type} `{name}` from Cloudband's AIM tool function? Provide a high-level explanation."
]

hybrid_input_options = [
    "Given the {element_type} `{name}` located at `{file_location}`, provide both a description and example code for its functionality, including calls: {calls}{decorators_text}. Here’s the code:\n\n{code}",
    "For the {element_type} `{name}` in AIM at {file_location}, summarize its purpose, list the methods it uses (calls: {calls}), {decorators_text}. Include the code:\n\n{code}",
    "Combine a high-level overview of the {element_type} `{name}` (file: {file_location}) with code snippets and explanations. Include dependencies: {dependencies}{decorators_text}, and the code:\n\n{code}"
]


def generate_random_input(template_options, decorators, **kwargs):
    """Generate a randomized input string from template options."""
    # Conditionally include decorators text
    if decorators:
        kwargs["decorators_text"] = f" and has the following decorators: {decorators}"
    else:
        kwargs["decorators_text"] = ""

    template = random.choice(template_options)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template.format_map({key: kwargs.get(key, 'None') for key in kwargs})


def extract_assistant_text(text):
    # Use regex to find the text between <assistant> and </s>
    matches = re.findall(r'<assistant>(.*?)</s>', text, re.DOTALL)
    return ' '.join(matches).strip()


def ask_llm(input_text):
    """Send a request to the LLM API to generate prompts based on the provided documentation and code."""
    response = requests.post(
        "http://127.0.0.1:443/api/backend/inference",
        json={"prompt": f"<user>{input_text}<assistant>", "contextLength": "32768"},
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
    if num_tokens > 32768:
        print(f"input number of tokens is bigger than 32768, skipping")
        return True
    return False


def process_element(element_data, element_type="element"):
    """Process a class, method, or function element by generating different types of inputs and corresponding outputs."""
    dataset = []
    name = element_data.get("class_name", "Unnamed") if element_type == "class" else element_data.get("function_name",
                                                                                                      "Unnamed")
    code = element_data.get("code", "")
    file_location = element_data.get("file_location", "Unknown")
    dependencies = element_data.get("dependencies", {}).get("imports", [])
    calls = element_data.get("calls", [])
    decorators = [decorator.get("decorator_function", "") for decorator in element_data.get("decorators", [])]

    # (1) Code as Input (with dependencies, file location, calls, decorators)
    code_based_input = generate_random_input(
        code_input_options,
        element_type=element_type,
        name=name,
        code=code,
        file_location=file_location,
        dependencies=', '.join(dependencies) if dependencies else 'None',
        calls=', '.join(calls) if calls else 'None',
        decorators=', '.join(decorators) if decorators else ''
    )

    if not is_more_than_ctx(code_based_input):
        code_based_output = {
            "code": code,
            "description": ask_llm(code_based_input),
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
                                        file_location=file_location,
                                        decorators=', '.join(decorators) if decorators else '')

    if not is_more_than_ctx(human_input):
        human_output = {
            "description": ask_llm(human_input),
            "code": code,
            "dependencies": dependencies,
            "decorators": decorators,
            "file_location": file_location
        }
        dataset.append({"input": human_input, "output": human_output, "type": "human_output"})

    # (3) Hybrid Input (with additional context)
    hybrid_input = generate_random_input(
        hybrid_input_options,
        element_type=element_type,
        name=name,
        code=code,
        file_location=file_location,
        dependencies=', '.join(dependencies),
        calls=', '.join(calls),
        decorators=', '.join(decorators)
    )

    if not is_more_than_ctx(human_input):
        hybrid_output = {
            "description": ask_llm(hybrid_input),
            "code": code,
            "dependencies": dependencies,
            "calls": calls,
            "decorators": decorators,
            "file_location": file_location
        }
        dataset.append({"input": hybrid_input, "output": hybrid_output, "type": "hybrid_output"})

    return dataset


def process_class_methods(class_data):
    """Process methods inside a class."""
    dataset = []
    methods = class_data.get("methods", [])
    for method_data in methods:
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
