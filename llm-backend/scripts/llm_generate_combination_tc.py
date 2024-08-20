import json
import os
import requests
import re
import ast


def get_template(element):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code.
    """
    # Template for the request
    request_template = f"""I have a list of three test cases, where each test case is represented as a JSON object. Each JSON object has a key that represents the test name, and the value is a list of dictionaries. Each dictionary in this list has two keys: "name" (the name of the test case) and "documentation" (a description of the test case).

Here are the three test cases:

{element}

List of test cases with their names and documentation.
Task:
Create a single, unified test by selecting and logically combining no more than 5 relevant steps from the three provided tests. The resulting test should be coherent, logical, and make sense in the context of testing. The combined test should include a sequence of steps from the original test cases.

Requirements:
Logical Combination: Ensure that the combination of the test cases results in a coherent and valid test sequence.
Retain Original Information: For each step in the combined test, include an indication of which original test case it came from.
Logical Order: The order of the resulting test case must be logical and in a correct sequence.
Max Length: The combined test must contain 1-20 steps.

Condition:
If it's not possible to logically combine the test cases into a coherent sequence, return an empty list.

Output Format:
resulted_list=[
    ("combined_test_case_step_1", "original_test_name_1"),
    ("combined_test_case_step_2", "original_test_name_2"),
    ("combined_test_case_step_3", "original_test_name_3"),
    ...
]

Generate a single, logically combined test, ensuring that the steps are coherent, relevant, and limited to exactly 1-20 steps. If this is not possible, return an empty list.
"""

    # Format the request
    return request_template


def send_request_to_llm(element):
    """
    Send a request to the LLM API to generate prompts based on the provided documentation and code.
    """
    # Template for the request
    prompt = get_template(element)
    # Send the request to the LLM API
    try:
        response = requests.post(
            "http://127.0.0.1:443/api/backend/inference",
            # Make sure to use 'http://' for local testing unless using HTTPS
            json={"prompt": prompt,
                  "contextLength": "8192"}
        )
        # Raise an error if the request failed
        response.raise_for_status()
        # Extract the response text
        return response.text  # Use response.text to get the string output
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None


def extract_latest_response_list(response_text):
    # Regex pattern that captures lists, excluding those with '...'
    pattern = r'resulted_list\s*=\s*\[(?!.*\.\.\.)(.*?)\]'
    matches = re.findall(pattern, response_text, re.DOTALL)

    if matches:
        # Get the last match, which should be the latest list
        list_str = matches[-1]
        list_str = f"[{list_str}]"  # Re-add the brackets around the captured content

        try:
            # Safely evaluate the list string using ast.literal_eval
            resulted_list = ast.literal_eval(list_str)
            return resulted_list
        except (SyntaxError, ValueError):
            return None  # In case of error, return None

    return None

# File paths
input_file = r'/home/instruct/testgenie/llm-backend/scripts/combination_lists_test_cases.json'
output_file = '/home/instruct/testgenie/llm-backend/scripts/test_cases.json'

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
processed_ids = len(processed_data)
start_index = processed_ids - 1 if processed_ids != 0 else 0

# Process each element in the dataset
for i, element in enumerate(data[start_index:], start=start_index):
    try:
        response_text = send_request_to_llm(element)

        if response_text:
            res_list = extract_latest_response_list(response_text)

            print(
                f"************************************************************ Test {i} ************************************************************")
            print(res_list)
            if res_list:
                print(len(res_list))
            else:
                print("tes list is None")
            print()
            processed_data.append(res_list)

            # Save progress after each successful element
            with open(output_file, 'w') as outfile:
                json.dump(processed_data, outfile, indent=4)

            print(f"Processed element {i + 1}/{len(data)}")
        else:
            print(f"Failed to generate prompts for element {i + 1}.")
            break  # Exit loop on failure to address the issue manually

    except Exception as e:
        print(f"Error processing element {i + 1}: {e}")
        # Optionally log the error to a file
        break  # Exit loop on failure to address the issue manually

print("Processing complete.")
