# import json
# from datasets import load_dataset
#
#
# def make_go_completion_pairs(imports_code, file_code, file_name, element_file_location, element_type):
#     """
#     Given the imports (string), code (string), file name, and element type,
#     produce a single dict with "input" and "output" for an 80/20 split
#     of the total code string.
#
#     The 'input' will contain triple-backtick Go code blocks,
#     and the 'output' will also be enclosed in triple-backtick Go.
#     """
#     # Combine the code components
#     imports = f"/* IMPORTS: {imports_code}*/\n\n" if imports_code else "\n"
#     full_code = f"// FILE: {element_file_location}\n" \
#                 f"// ELEMENT TYPE: {element_type}\n" \
#                 f"{imports}" \
#                 f"{file_code}"
#
#     total_length = len(full_code)
#
#     # If the combined code length is less than 10 characters, skip it
#     if total_length < 10:
#         return []
#
#     # Calculate the split index (80% for input, 20% for output)
#     split_index = int(total_length * 0.8)
#
#     # Create prompt and completion
#     prompt_text = full_code[:split_index]
#     completion_text = full_code[split_index:]
#
#     # Build the example
#     example = {
#         "input": f"""complete the following {element_type}:
# ```typescript\n{prompt_text}\n```""",
#         "output": f"```typescript\n{completion_text}\n```"
#     }
#
#     return [example]
#
#
# def main():
#     # 1. Load your dataset from Hugging Face
#     dataset = load_dataset("oodeh/MTA-tests", data_files="tackle2_ui.json", split="train")
#
#     # 2. List to hold all final examples
#     completion_pairs = []
#
#     # 3. Iterate over each record
#     for record in dataset:
#         # Expecting: { "name": ..., "code": ..., "imports": ..., "element_type": ..., "file_location": ... }
#         element_name = record.get("name", "")
#         element_file_location = record.get("file_location", "")
#         element_code = record.get("code", "")
#         element_imports = record.get("imports", "")
#         element_type = record.get("element_type", "unknown element")
#
#         if element_type.lower() == "file":
#             continue
#
#         # Create prompt-completion pairs
#         pairs = make_go_completion_pairs(element_imports, element_code, element_name, element_file_location,
#                                          element_type)
#         completion_pairs.extend(pairs)
#
#     # 4. Write to a JSON file
#     with open("typescript_code_completion_dataset.json", "w", encoding="utf-8") as f:
#         json.dump(completion_pairs, f, indent=2, ensure_ascii=False)
#
#     print(f"Created typescript_code_completion_dataset.json with {len(completion_pairs)} examples.")
#
#
# if __name__ == "__main__":
#     main()
#
#


import json
import random
from datasets import load_dataset

def fetch_json_from_dataset(repo_id, file_name):
    """Fetch a JSON file from a Hugging Face dataset."""
    dataset = load_dataset(repo_id, data_files=file_name, split="train")
    return dataset

def merge_json_files(hf_data, local_file_path, output_file_path):
    """Merge the JSON data from Hugging Face and a local file."""
    # Initialize the new list to store the merged data
    merged_data = []

    # Process Hugging Face data
    for obj in hf_data:
        if "input_text" in obj and "output_text" in obj:
            merged_data.append({
                "input": obj["input_text"],
                "output": obj["output_text"]
            })

    # Process local JSON file
    with open(local_file_path, 'r') as f:
        local_data = json.load(f)
        for obj in local_data:
            merged_data.append(obj)

    # Shuffle the merged data
    random.shuffle(merged_data)

    # Export the merged data to a new JSON file
    with open(output_file_path, 'w') as f:
        json.dump(merged_data, f, indent=4)

    print(f"Merged data exported to {output_file_path}")

if __name__ == "__main__":
    # Hugging Face dataset details
    repo_id = "oodeh/MTA-tests"
    hf_file_name = "tackle2_ui_prompt_lab.json"

    # Fetch data from the Hugging Face dataset
    print("Fetching file from Hugging Face dataset...")
    hf_data = fetch_json_from_dataset(repo_id, hf_file_name)

    # Local file path
    local_file_path = "typescript_code_completion_dataset.json"

    # Output file path
    output_file_path = "mta_ui_dataset.json"

    # Merge and process
    merge_json_files(hf_data, local_file_path, output_file_path)
