import os
import json
import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander
from meta_data.helpers.meta_data_extractor import MetaDataExtractor
from meta_data.helpers.meta_data_query_expander import MetaDataQueryExpander

def read_file(file_path):
    """
    Reads a JSON file and returns its content as a Python object.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file at {file_path}")
        sys.exit(1)


def main():
    # Path to the JSON file containing parsed objects
    file_path = os.path.join(os.path.dirname(__file__), "kubevirt_replicaset.json")
    parsed_elements = read_file(file_path)

    project_meta_expander = MetaDataProjectExpander(
        parsed_elements=parsed_elements,
        project_name="kubevirt",
        project_repo_path="https://github.com/kubevirt/kubevirt",
        project_programming_languages=["Go"]
    )

    # Add metadata to each parsed element & Add the entire elements to the DB
    project_meta_expander.add_metadata()
    project_meta_expander.add_to_db()

    query_meta_expander = MetaDataQueryExpander(
        query="default query",
        model_name="default_model",
        model_id="model_id_123"
    )

    # Extract metadata for the query
    query_metadata = query_meta_expander.extract_metadata()
    print("Extracted Query Metadata:", json.dumps(query_metadata, indent=4))


if __name__ == "__main__":
    main()

# From 'AI-TC-s-Generator/data-pre' we can run the script with the following command: 'python -m meta_data.main'
# Steps to Access MongoDB Through SSH Tunneling: "ssh -L 27018:localhost:27017 user@VM_IP" (ssh -L 27018:localhost:27017 cloud-user@10.46.249.22)
# Connect to MongoDB Using MongoDB Compass: "mongodb://localhost:27018/
# Optional: Keep the Tunnel Open: "ssh -f -N -L 27018:localhost:27017 user@VM_IP" (-f runs SSH in the background, -N tells SSH not to execute commands on the remote host)