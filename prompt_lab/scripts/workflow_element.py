import os
import json
from transformers import AutoTokenizer  # Import the tokenizer

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")


# Function to read the content of a file
def read_file_content(file_path):
    with open(file_path, "r") as file:
        return file.read()


# Function to count tokens using the specified tokenizer
def count_tokens(content):
    tokens = tokenizer.encode(content, truncation=False)
    return len(tokens)


# Main function to create the workflows data
def create_workflow_data(base_dir):
    workflows_data = []

    # Iterate through directories
    for root, dirs, files in os.walk(base_dir):
        if "application.properties" in files:
            # Read the application.properties file
            properties_file_path = os.path.join(root, "application.properties")
            properties_content = read_file_content(properties_file_path)
            properties_token_count = count_tokens(properties_content)

            # Check for workflows in the current directory
            workflows = [f for f in files if f.endswith((".sw.json", ".sw.yaml"))]
            for workflow in workflows:
                workflow_file_path = os.path.join(root, workflow)
                workflow_content = read_file_content(workflow_file_path)
                workflow_format = "json" if workflow.endswith(".json") else "yaml"
                workflow_name = os.path.splitext(os.path.splitext(workflow)[0])[0]

                workflow_data = {
                    "name": workflow_name,
                    "workflow": f"```{workflow_format}\n{workflow_content}\n```",  # Add the workflow content
                    "properties": properties_content,  # No format prefix
                    "schemas": [],
                    "specs": [],
                    "element_type": "workflow"
                }

                # Look for schemas
                schemas_path = os.path.join(root, "schemas")
                if os.path.exists(schemas_path) and os.path.isdir(schemas_path):
                    for schema_file in os.listdir(schemas_path):
                        schema_file_path = os.path.join(schemas_path, schema_file)
                        schema_content = read_file_content(schema_file_path)
                        workflow_data["schemas"].append({
                            "file": os.path.join(os.path.basename(schemas_path), os.path.basename(schema_file_path)),
                            "content": f"```yaml\n{schema_content}\n```" if schema_file.endswith(
                                ".yaml") else f"```json\n{schema_content}\n```",
                        })

                # Look for specifications
                specs_path = os.path.join(root, "specs")
                if os.path.exists(specs_path) and os.path.isdir(specs_path):
                    for spec_file in os.listdir(specs_path):
                        spec_file_path = os.path.join(specs_path, spec_file)
                        spec_content = read_file_content(spec_file_path)
                        spec_token_count = count_tokens(spec_content)

                        # Skip the spec if it exceeds the token limit
                        if spec_token_count <= 8192:
                            workflow_data["specs"].append({
                                "file": os.path.join(os.path.basename(specs_path), os.path.basename(spec_file_path)),
                                "content": f"```yaml\n{spec_content}\n```" if spec_file.endswith(
                                    ".yaml") else f"```json\n{spec_content}\n```",
                            })
                        else:
                            print(f"{os.path.relpath(spec_file_path, base_dir)} spec token is {spec_token_count}")

                # Calculate the total token count for the workflow element
                total_tokens = properties_token_count
                total_tokens += count_tokens(workflow_content)
                total_tokens += sum(count_tokens(schema["content"]) for schema in workflow_data["schemas"])
                total_tokens += sum(count_tokens(spec["content"]) for spec in workflow_data["specs"])

                workflows_data.append(workflow_data)

                # Print the token count for the workflow element
                print(f"Workflow '{workflow_name}' Total Tokens: {total_tokens}")

    return workflows_data


# Save data to JSON
def save_data(data, output_json):
    with open(output_json, "w") as json_file:
        json.dump(data, json_file, indent=4)


# Main script
if __name__ == "__main__":
    base_directory = "serverless-workflow-examples-ai"  # Replace with the path to your workflows directory
    output_json_file = "workflows.json"

    workflows = create_workflow_data(base_directory)
    save_data(workflows, output_json_file)

    print(f"Workflows data saved to {output_json_file}.")
