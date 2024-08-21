import json
import os
import requests


def robot_test_template(test_name, code):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code
    using the updated instruction set for prompt creation.
    """
    request_template = f"""
    I have a code snippet for a Go test that is part of the Cluster Node Tuning Operator project. 
    I need to generate two distinct prompts to train a language model. 
    The prompts should clearly and instructively describe the functionality of the code and the general purpose of the test, 
    enabling the model to generate the code snippet as output. Each prompt should be unique 
    to add diversity and versatility to the dataset.
    
    Here is an example of a dataset element:
    
    Test name: {test_name}
    
    Code: "{code}"
    
    Please transform the Code into two distinct prompts that a language model can use to generate the corresponding code. 
    The prompts should be detailed enough to guide the model in generating the correct code and to explain the overall purpose of the test. 
    Ensure that the prompts cover different aspects or perspectives of the task described by the Code and how it reflects the test's objectives.
    
    **Important:**
    - Each prompt must explicitly mention that the code is for a Go test and is part of the Cluster Node Tuning Operator project.
    - Prompt 1 should present the instructions in a step-by-step format using a numbered list. The list should include both detailed instructions and an explanation of the test's purpose.
    - Prompt 2 should be in a continuous free-text narrative, without using any numbered lists or explicit step indicators. 
    Focus on describing the code and the test's purpose in a flowing, narrative manner that reads like a paragraph, explaining the logic, purpose, and context without breaking it down into steps.
    
    Format the output as follows, and return only the output. The two prompts should be distinct and do not know about each other:
    
    Prompt 1: <First prompt here>
    Prompt 2: <Second prompt here>
    """

    return request_template


def full_test_template(documentation, code):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code
    using the updated instruction set for prompt creation.
    """
    # Updated template for the request
    # request_template = (
    #     "I have documentation and a corresponding code snippet. "
    #     "I need to generate two distinct prompts to train a language model. "
    #     "The prompts should clearly and instructively describe the functionality of the code, "
    #     "enabling the model to generate the code snippet as output. Each prompt should be unique "
    #     "to add diversity and versatility to the dataset.\n\n"
    #     "Here is an example of a dataset element:\n\n"
    #     "Documentation: {}\n"
    #     "Code: {}\n\n"
    #     "Please transform the documentation into two distinct prompts that a language model can use to generate the corresponding code. "
    #     "The prompts should be detailed enough to guide the model in generating the correct code. "
    #     "Ensure that the prompts cover different aspects or perspectives of the task described by the documentation.\n\n"
    #     "**Important:**\n"
    #     "- Each prompt must explicitly mention that the code is for a Robot Framework test and is part of the NCS project.\n"
    #     "- Prompt 1 should present the instructions in a step-by-step format using a numbered list.\n"
    #     "- Prompt 2 should be in a continuous free text narrative, without using any numbered lists or explicit step indicators. "
    #     "Focus on describing the code in a flowing, narrative manner that reads like a paragraph, explaining the logic, purpose, and context without breaking it down into steps.\n\n"
    #     "Format the output as follows, and return only the output. The two prompts should be distinct and do not know about each other:\n\n"
    #     "Prompt 1: <First prompt here>\n"
    #     "Prompt 2: <Second prompt here>"
    # )
    request_template = (
        "I have code snippet. "
        "I need to generate two distinct prompts to train a language model. "
        "The prompts should clearly and instructively describe the functionality of the code and the general purpose of the test, "
        "enabling the model to generate the code snippet as output. Each prompt should be unique "
        "to add diversity and versatility to the dataset.\n\n"
        "Here is an example of a dataset element:\n\n"
        "Code: {}\n\n"
        "Please transform the Code into two distinct prompts that a language model can use to generate the corresponding code. "
        "The prompts should be detailed enough to guide the model in generating the correct code and to explain the overall purpose of the test. "
        "Ensure that the prompts cover different aspects or perspectives of the task described by the Code and how it reflects the test's objectives.\n\n"
        "**Important:**\n"
        "- Each prompt must explicitly mention that the code is for a Robot Framework test and is part of the NCS project.\n"
        "- Prompt 1 should present the instructions in a step-by-step format using a numbered list. The list should include both detailed instructions and an explanation of the test's purpose.\n"
        "- Prompt 2 should be in a continuous free-text narrative, without using any numbered lists or explicit step indicators. "
        "Focus on describing the code and the test's purpose in a flowing, narrative manner that reads like a paragraph, explaining the logic, purpose, and context without breaking it down into steps.\n\n"
        "Format the output as follows, and return only the output. The two prompts should be distinct and do not know about each other:\n\n"
        "Prompt 1: <First prompt here>\n"
        "Prompt 2: <Second prompt here>"
    )

    return request_template.format(code)


def test_case_template(documentation, code):
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
    return request_template.format(documentation, code)


def send_request_to_llm(test_name, code):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code.
    """
    # Template for the request
    # prompt = test_case_template(documentation, code)
    prompt = robot_test_template(test_name, code)
    print(prompt)
    # Send the request to the LLM API
    try:
        response = requests.post(
            "http://127.0.0.1:443/api/backend/inference",
            # Make sure to use 'http://' for local testing unless using HTTPS
            json={"prompt": prompt,
                  "contextLength": "32768"}
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
    lines = response_text.splitlines()

    prompt_1_lines = []
    prompt_2_lines = []

    current_prompt = None

    # Iterate through lines to find prompts
    for line in lines:
        if line.startswith("Prompt 1:"):
            current_prompt = prompt_1_lines
            # Start collecting lines for Prompt 1, ignoring any placeholder text
            content = line.split(":", 1)[1].strip()
            if content:
                current_prompt.append(content)
        elif line.startswith("Prompt 2:"):
            current_prompt = prompt_2_lines
            # Start collecting lines for Prompt 2, ignoring any placeholder text
            content = line.split(":", 1)[1].strip()
            if content:
                current_prompt.append(content)
        elif current_prompt is not None:
            # Add lines to the current prompt until a new prompt begins
            current_prompt.append(line.strip())

    # Join the collected lines for each prompt and clean up
    prompt_1 = "\n".join(prompt_1_lines).replace("</s>", "").strip()
    prompt_2 = "\n".join(prompt_2_lines).replace("</s>", "").strip()

    # Remove placeholder text and unnecessary markers that may have been incorrectly captured
    prompt_1 = prompt_1.replace("<First prompt here>", "").replace("---", "").strip()
    prompt_2 = prompt_2.replace("<Second prompt here>", "").replace("---", "").strip()

    return prompt_1, prompt_2


# File paths
input_file = '/home/instruct/GO_tests_mapping.json'
output_file = 'go_tests_2_prompts.json'

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
processed_ids = {item['test_name'] for item in processed_data}
start_index = next((i for i, test_name in enumerate(data.keys()) if test_name not in processed_ids), len(data))

# Process each element in the dataset
for i, test_name in enumerate(list(data.keys())[start_index:], start=start_index):
    code = data[test_name]
    try:
        # Generate prompts using the LLM API
        # response_text = send_request_to_llm(documentation, code)
        response_text = send_request_to_llm(test_name, code)

        if response_text:
            # Extract prompts from the response
            prompt_1, prompt_2 = extract_prompts(response_text)

            # Create a new element with prompts
            new_element = {
                "test_name": test_name,
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

            print(f"Processed element {i + 1}/{len(list(data.keys()))}")
        else:
            print(f"Failed to generate prompts for element {i + 1}.")
            break  # Exit loop on failure to address the issue manually

    except Exception as e:
        print(f"Error processing element {i + 1}: {e}")
        # Optionally log the error to a file
        break  # Exit loop on failure to address the issue manually

print("Processing complete.")
