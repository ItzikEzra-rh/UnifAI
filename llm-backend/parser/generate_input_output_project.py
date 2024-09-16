import random

# Code as Input Options (Generic for Classes, Methods, Functions)
code_input_options = [
    "{element_type} `{name}` is part of the AIM tool in Cloudband, located at `{file_location}`. It relies on the following dependencies: {dependencies}. Describe its functionality:\n\n{code}",
    "Explain the purpose and functionality of the {element_type} `{name}` from the AIM tool in Cloudband, which is located at `{file_location}`. It uses the following calls: {calls} and has the following decorators: {decorators}. Code:\n\n{code}",
    "Analyze the {element_type} `{name}` in the AIM Cloudband project (file: {file_location}). This element depends on {dependencies} and uses the following calls: {calls}. Provide a detailed explanation of its purpose. Here's the code:\n\n{code}"
]

human_input_options = [
    "What is the purpose of the {element_type} `{name}` located at `{file_location}` in the AIM project?",
    "Explain the role of the {element_type} `{name}` in the AIM tool and how it interacts with other parts of the project (file: {file_location}).",
    "How does the {element_type} `{name}` from Cloudband's AIM tool function? Provide a high-level explanation."
]

hybrid_input_options = [
    "Given the {element_type} `{name}` located at `{file_location}`, provide both a description and example code for its functionality, including calls: {calls} and decorators: {decorators}. Here’s the code:\n\n{code}",
    "For the {element_type} `{name}` in AIM at {file_location}, summarize its purpose, list the methods it uses (calls: {calls}), and explain its decorators: {decorators}. Include the code:\n\n{code}",
    "Combine a high-level overview of the {element_type} `{name}` (file: {file_location}) with code snippets and explanations. Include dependencies: {dependencies}, decorators: {decorators}, and the code:\n\n{code}"
]


def generate_random_input(template_options, **kwargs):
    """Generate a randomized input string from template options."""
    template = random.choice(template_options)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template.format_map({key: kwargs.get(key, 'None') for key in kwargs})


def ask_llm(input_text):
    """Placeholder for calling the LLM with input text."""
    # In actual implementation, this function will make a call to an LLM
    return f"Generated description for: {input_text}"


def process_element(element_data, element_type="element"):
    """
    Process a class, method, or function element by generating different types of inputs and corresponding outputs.
    """
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
        decorators=', '.join(decorators) if decorators else 'None'
    )

    code_based_output = {
        "code": code,
        "description": ask_llm(code_based_input),  # Calling the LLM to generate the description
        "dependencies": dependencies,
        "calls": calls,
        "decorators": decorators,
        "file_location": file_location
    }
    dataset.append({
        "input": code_based_input,
        "output": code_based_output
    })

    # (2) Human-Level Input
    human_input = generate_random_input(human_input_options, element_type=element_type, name=name,
                                        file_location=file_location)
    human_output = {
        "description": ask_llm(human_input),
        "code": code,
        "dependencies": dependencies,
        "decorators": decorators,
        "file_location": file_location
    }
    dataset.append({
        "input": human_input,
        "output": human_output
    })

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

    hybrid_output = {
        "description": ask_llm(hybrid_input),
        "code": code,
        "dependencies": dependencies,
        "calls": calls,
        "decorators": decorators,
        "file_location": file_location
    }
    dataset.append({
        "input": hybrid_input,
        "output": hybrid_output
    })

    return dataset


def process_json(json_data):
    """
    Process the entire JSON dataset, extracting classes, methods, and functions to create diverse LLM training datasets.
    """
    full_dataset = []

    # Process Classes
    for class_data in json_data.get("classes", []):
        full_dataset.extend(process_element(class_data, element_type="class"))

    # Process Functions
    for function_data in json_data.get("functions", []):
        full_dataset.extend(process_element(function_data, element_type="function"))

    return full_dataset

# Example Usage
# json_data = {...}  # Your JSON data here
# dataset = process_json(json_data)
# print(dataset)
