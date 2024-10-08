import json
import random
import requests
import re
import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("unsloth/mistral-7b-instruct-v0.3-bnb-4bit")

structured_prompt = """Transform the following Robot Framework test code into a prompt for a language model to generate the same code.  

Test code: "{code}"

The prompt should reflect the step-by-step structure of the code in a simple and user-friendly way:

"Generate a Robot Framework test specifically for the ODS-CI project by following these easy steps:
- Step 1: Start with the main action, and clearly mention that it’s for a Robot Framework test in the ODS-CI project.
- Step 2: Move on to the next action, explaining how it fits into the Robot Framework test for ODS-CI.
- Step 3: Keep going through the rest of the actions, just giving a sense of what’s happening at each step, always highlighting that this is for the ODS-CI project.
Keep the steps clear and easy to follow, so it’s like telling a friend how to set up the test for the Robot Framework in ODS-CI without going into too much detail."
"""

descriptive_prompt = """Transform the following Robot Framework test code into a prompt for a language model to generate the same code.  

Test code: "{code}"

The prompt should describe the code as a friendly, flowing narrative:

"Write a Robot Framework test for the ODS-CI project, and make sure to describe it in a way that feels like you’re telling someone about a test designed specifically for this purpose. Talk about how each action contributes to the Robot Framework test within ODS-CI. Describe the actions in a natural, easy-going way, focusing on how they all come together to create a complete test for the Robot Framework in the context of the ODS-CI project, as a continuous story."
"""

creative_prompt = """Transform the following Robot Framework test code into a prompt for a language model to generate the same code.  

Test code: "{code}"

The prompt should give a high-level overview in a friendly tone:

"Imagine you’re describing this Robot Framework test for the ODS-CI project, and be sure to mention it’s specifically designed for this context. Explain what the test is all about in simple terms, keeping in mind that it’s a Robot Framework test tailored for ODS-CI. Describe the main goals and why the test matters for ODS-CI without diving into steps. Just give a big-picture view of how this Robot Framework test works within ODS-CI, like you’re summarizing it for someone who’s curious."
"""

human_prompt = """Transform the following Robot Framework test code into a prompt for a language model to generate the same code.  

Test code: "{code}"

The prompt should reflect a human giving a direct request to create a test, using natural, plain language. Avoid including any specific examples or technical details:

"Create a Robot Framework test for the ODS-CI project. The test should check connections, verify access, and ensure cleanup at the end. Describe the overall goals, such as setting up connections, confirming that access is working as expected, and making sure everything is wrapped up afterward. Keep it high-level, without detailed steps or code, as if you're asking someone to set up and validate these processes in ODS-CI."

**Requirement:** The prompt should read like a human is asking the model to create or generate a test. It must not include code or highly technical details, and should focus on describing the test requirements in simple, everyday language.
"""
input_options = [structured_prompt, descriptive_prompt, creative_prompt, human_prompt]


def generate_random_input(template_options, **kwargs):
    """Generate a randomized input string from template options."""
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
    if num_tokens > 32768:
        print(f"input number of tokens is bigger than 32768, skipping")
        return True
    return False


def process_element(element_data):
    """Process a Keyword, Resource, Test_Case, or Test element."""
    dataset = []
    file_location = element_data[0]
    code = element_data[1]

    # Generate inputs and outputs
    for input_template in input_options:
        input_text = input_template.format(code=code)

        prompt = f"<user>{input_text}</user><assistant>"

        _input = ask_llm(prompt)
        dataset.append(
            {"input": _input, "output": code, "element_type": "Test", 'file_location': file_location})

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
    for idx, test_tuple in enumerate(json_data, start=1):
        print(f"************************** {idx}/{total_elements} ***************************************")
        if idx < current_index:  # Skip elements already processed
            continue
        # Process the file and its elements itself
        full_dataset.extend(process_element(test_tuple))

        current_index = idx
        save_progress(current_index, full_dataset, progress_file)

    return full_dataset


# File paths
json_file_path = r"/home/instruct/AI-TC-s-Generator/llm-backend/scripts/RHOAI_tests_mapping.json"
output_file = r"/home/instruct/AI-TC-s-Generator/llm-backend/scripts/RHOAI_tests_prompts.json"
progress_file = r"//home/instruct/AI-TC-s-Generator/llm-backend/scripts/progress.json"

# Load JSON data
with open(json_file_path, 'r') as f:
    json_data = json.load(f)
    data = list(json_data.items())

# Process the JSON and save the dataset
process_json(data, output_file, progress_file)
