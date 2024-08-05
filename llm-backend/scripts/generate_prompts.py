import json
import os
import requests


def send_request_to_llm(documentation, code):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code.
    """
    # Template for the request
    request_template = (
        "I have a documentation and corresponding code snippet. "
        "I need to generate two different prompts that will be used to train a language model. "
        "The prompts should describe the functionality of the code clearly and instructively, allowing the model to generate the code snippet as output. "
        "Each prompt should be unique to add diversity and versatility to the dataset.\n\n"
        "Here is an example of a dataset element:\n\n"
        "Documentation: {}\n"
        "Code: {}\n\n"
        "Please transform the documentation into two distinct prompts that a language model can use to generate the corresponding code. "
        "The prompts should be detailed enough to guide the model in generating the correct code. "
        "Ensure that the prompts cover different aspects or perspectives of the task described by the documentation.\n\n"
        "**Important:** Each prompt must explicitly mention that the code is for a Robot Framework test and is part of the NCS project.\n\n"
        "Format the output as follows, and return only the output:\n"
        "Prompt 1: <First prompt here>\n"
        "Prompt 2: <Second prompt here>"
    )

    # Format the request
    prompt = request_template.format(documentation, code)

    # Send the request to the LLM API
    try:
        response = requests.post(
            "http://127.0.0.1:443/api/backend/inference",
            # Make sure to use 'http://' for local testing unless using HTTPS
            json={"prompt": prompt}
        )
        # Raise an error if the request failed
        response.raise_for_status()
        # Extract the response text
        return response.text  # Use response.text to get the string output
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None


def extract_prompts(response_text):
    """
    Extract Prompt 1 and Prompt 2 from the LLM response text.
    """
    # Split the text to find the lines containing the prompts
    lines = response_text.splitlines()

    prompt_1 = ""
    prompt_2 = ""

    # Iterate through lines to find prompts
    for line in lines:
        if line.startswith("Prompt 1:"):
            prompt_1 = line.split(":", 1)[1].strip()  # Extract text after "Prompt 1:"
        elif line.startswith("Prompt 2:"):
            prompt_2 = line.split(":", 1)[1].strip()  # Extract text after "Prompt 2:"

    return prompt_1.replace("</s>", "").strip(), prompt_2.replace("</s>", "").strip()


# File paths
input_file = '/home/instruct/ncs_8343_test_cases_doc.json'
output_file = 'ncs_8343_test_cases_documentation_prompts.json'

# Load the input dataset
with open(input_file, 'r') as infile:
    data = json.load(infile)

# Load existing progress if available
if os.path.exists(output_file):
    with open(output_file, 'r') as outfile:
        processed_data = json.load(outfile)
else:
    processed_data = []

# Determine starting point
processed_ids = {item['documentation'] for item in processed_data}
start_index = next((i for i, item in enumerate(data) if item['documentation'] not in processed_ids), len(data))

# Process each element in the dataset
for i, element in enumerate(data[start_index:], start=start_index):
    documentation = element['documentation']
    code = element['code']

    try:
        # Generate prompts using the LLM API
        response_text = send_request_to_llm(documentation, code)
        # print(response_text)
        if response_text:
            # Extract prompts from the response
            prompt_1, prompt_2 = extract_prompts(response_text)

            # Create a new element with prompts
            new_element = {
                "documentation": documentation,
                "code": code,
                "prompt_1": prompt_1,
                "prompt_2": prompt_2
            }
            print(
                f"************************************************************ Test case {i} ************************************************************")
            print(f"prompt1: {prompt_1}")
            print(f"prompt2: {prompt_2}")
            print()
            print()
            processed_data.append(new_element)

            # Save progress after each successful element
            with open(output_file, 'w') as outfile:
                json.dump(processed_data, outfile, indent=4)

            print(f"Processed element {i + 1}/{len(data)}: {documentation}")
        else:
            print(f"Failed to generate prompts for element {i + 1}.")
            break  # Exit loop on failure to address the issue manually

    except Exception as e:
        print(f"Error processing element {i + 1}: {e}")
        # Optionally log the error to a file
        break  # Exit loop on failure to address the issue manually

print("Processing complete.")
