import json
import requests
from transformers import AutoTokenizer
import string
import copy

# Configuration
INPUT_FILE_PATH = "data/serverless_Workflows_parsed_processed.json"  # Path to the JSON file with elements
PASSED_FILE_PATH = "data/passed.json"  # Path to save elements that passed
FAILED_FILE_PATH = "data/failed.json"  # Path to save elements that failed
API_URL = "http://0.0.0.0:8000/v1/completions"  # API URL for LLM
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
BATCH_SIZE_LIMIT = 8
MAX_TOKENS = 2  # Limit to a small number to encourage single number responses
MAX_CONTEXT_LEN = 8192
SCORE_THRESHOLD = 7

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def format_chat_prompt(system_message, context):
    """
    Formats the prompt in chat-style for the LLM.
    """
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": context}
    ]


def create_prompt(element):
    """
    Create a prompt for the LLM based on the input and output of the element.
    """
    system_message = (
        "You are a reviewer. Rate the output based on the following criteria, using a scale from 1 to 10. "
        "Respond with only a single number from 1 to 10, with no additional text or punctuation.\n\n"
        "Relevance: Assess how well the output addresses the input request. A high score reflects a strong, "
        "meaningful connection between the input and output.\n\n"
        "Absence of Hallucinations: Ensure the output does not contain irrelevant or invented information. "
        "This includes:\n"
        "- Repetitive phrases or nonsensical strings (e.g., ‘create bool create bool create bool’).\n"
        "- Incomplete or trailing sentences.\n"
        "- Sections of text that do not contribute meaningfully to the requested answer.\n"
        "Any presence of hallucinated content should result in a failing score.\n\n"
        "Quality: Evaluate the clarity, coherence, and completeness of the output. A high-quality response is "
        "well-structured, concise, and directly addresses the input without errors, unnecessary repetition, or "
        "extraneous information.\n\n"
        "Based on these criteria, provide only a single number from 1 to 10, without any additional characters."
    )

    input_text = element.get("input", "No input provided.")
    output_text = element.get("output", "No output provided.")
    context = f"Input: {input_text}\nOutput: {output_text}\n\nYour score (1-10):"

    # Return formatted prompt in chat format
    return format_chat_prompt(system_message, context)


def count_tokens(text):
    """
    Counts the number of tokens in a given text using the tokenizer.
    """
    tokens = tokenizer.encode(text, truncation=False)
    return len(tokens)


def send_request(prompts):
    """
    Send a batch of prompts to the LLM and return the responses.
    """
    data = {
        "model": MODEL_NAME,
        "prompt": prompts,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3
    }
    response = requests.post(API_URL, json=data, headers={"Content-Type": "application/json"})
    response.raise_for_status()

    return [choice["text"] for choice in sorted(response.json().get("choices", []), key=lambda x: x.get("index", 0))]


def _format_context(context_template, element):
    """
    Format the context template by ensuring each placeholder in the template
    is formatted only once.
    """
    element_copied = copy.deepcopy(element)

    # Parse placeholders from the template
    formatter = string.Formatter()
    placeholders = [field_name for _, field_name, _, _ in formatter.parse(context_template) if field_name]

    # Format each placeholder value if not already formatted
    for placeholder in placeholders:
        if element_copied.get(placeholder):
            value = element_copied[placeholder]
            # Check if the value is a string and starts with the formatted prefix
            if isinstance(value, str) and value.startswith(f"{placeholder}:\n"):
                continue  # Already formatted, skip
            # Format and update the placeholder
            element_copied[placeholder] = f"{placeholder}:\n{value}"
        else:
            element_copied[placeholder] = ""  # Default for missing placeholders

    # Format the context
    return context_template.format(**element_copied)


def main():
    # Load data
    with open(INPUT_FILE_PATH, "r") as f:
        elements = json.load(f)

    passed_elements = []
    failed_elements = []
    batch_prompts = []
    batch_metadata = []
    batch_index = 0
    batch_token_count = 0

    for i, element in enumerate(elements):
        prompt = create_prompt(element)
        prompt_text = tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
        prompt_token_count = count_tokens(prompt_text)

        # Skip if a single prompt exceeds max context length
        if prompt_token_count > MAX_CONTEXT_LEN - MAX_TOKENS:
            print(f"Skipping prompt with {prompt_token_count} tokens as it exceeds max context length.")
            failed_elements.append({"element": element,
                                    "score": None})
            continue

        # Add prompt to batch if within limits
        if (len(batch_prompts) < BATCH_SIZE_LIMIT) and (
                batch_token_count + prompt_token_count <= MAX_CONTEXT_LEN - MAX_TOKENS):
            batch_prompts.append(prompt_text)
            batch_metadata.append(element)
            batch_token_count += prompt_token_count
        else:
            # Process current batch if limits are reached
            print(f"Processing batch {batch_index + 1} with {len(batch_prompts)} prompts...")
            responses = send_request(batch_prompts)

            for meta, response in zip(batch_metadata, responses):
                try:
                    score = int(response.strip())  # Strip and parse as integer
                except ValueError:
                    print("parsing failed")
                    score = 0  # Default score if parsing fails

                # Print the question, answer, and score
                print("\n--- Review Summary ---")
                print(f"Question:\ninput:\n{meta['input']}\n\noutput:\n{meta['output']}")
                print(f"element: {i}")
                print(f"Answer: {response}")
                print(f"Score: {score}")

                if score >= SCORE_THRESHOLD:
                    passed_elements.append(meta)
                else:
                    failed_elements.append({"element": meta,
                                            "score": score})

            # Reset batch
            batch_prompts = [prompt_text]
            batch_metadata = [element]
            batch_token_count = prompt_token_count
            batch_index += 1

    # Process any remaining prompts in the final batch
    if batch_prompts:
        print(f"Processing final batch with {len(batch_prompts)} prompts...")
        responses = send_request(batch_prompts)

        for meta, response in zip(batch_metadata, responses):
            try:
                score = int(response.strip())  # Strip and parse as integer
            except ValueError:
                print("fail parsing")
                score = 0  # Default score if parsing fails

            # Print the question, answer, and score
            print("\n--- Review Summary ---")
            print(f"Question:\ninput:\n{meta['input']}\n\noutput:\n{meta['output']}")
            print(f"Answer: {response}")
            print(f"Score: {score}")

            if score >= SCORE_THRESHOLD:
                passed_elements.append(meta)
            else:
                failed_elements.append({"element": meta,
                                        "score": score})

    # Save passed and failed elements to separate files
    with open(PASSED_FILE_PATH, "w") as f:
        json.dump(passed_elements, f, indent=4)
    with open(FAILED_FILE_PATH, "w") as f:
        json.dump(failed_elements, f, indent=4)

    print(f"Processing complete. {len(passed_elements)} elements passed and {len(failed_elements)} elements failed.")


if __name__ == "__main__":
    main()
