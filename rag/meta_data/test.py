import os
import json
import sys
import re
from bson import json_util

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander
from meta_data.helpers.meta_data_query_expander import MetaDataQueryExpander
from meta_data.helpers.meta_data_retriever import MetaDataRetriever

def name_to_path_tuple_generator(data):
    result = []
    for item in data:
        name = item.get("name")
        location = item.get("location", "")

        # Extract location using regex
        match = re.search(r"File Location:\s*(.+)", location)
        if match:
            file_location = match.group(1).strip()
            result.append((name, file_location))

    return result

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

def add_project_metadata():
    # Path to the JSON file containing parsed objects
    file_path = os.path.join(os.path.dirname(__file__), "kubevirt_Mapping.json")
    file_path = "/home/cloud-user/Playground/TAG_Files/kubevirt_Mapping.json"
    parsed_elements = read_file(file_path)

    project_meta_expander = MetaDataProjectExpander(
        parsed_elements=parsed_elements,
        project_name="kubevirt",
        project_repo_path="https://github.com/kubevirt/kubevirt",
        naming_mapping ={'element_type': 'type', 'file_location': 'location', 'project_name': 'project_name'},
        built_in_keys =['element_type', 'file_location', 'project_name'],
        exclude_types =['File'],
        project_programming_languages=["Go"]
    )

    # Add metadata to each parsed element & Add the entire elements to the DB
    project_meta_expander.add_metadata()
    project_meta_expander.add_to_db()

def main():
    # add_project_metadata()

    query_meta_expander = MetaDataQueryExpander(
        # query="Please create a test case that create ReplicaSet & should update and verify readyReplicas once VMIs are up",
        query = "Please write a test case that checking the number of replicaset",
        # query = "Provide a code that use master replace",
        # query = "Provide a code that deploy security hardening",
        # query = "Provide a code that creates a persistentvolume",
        project_name="kubevirt",
        model_name="default_model",
        model_id="model_id_123"
    )

    # Extract metadata for the query
    query_metadata = query_meta_expander.extract_metadata()
    print("Extracted Query Metadata:", json.dumps(query_metadata, indent=4))

    meta_data_retreiver = MetaDataRetriever(query_metadata=query_metadata)
    best_match = meta_data_retreiver.best_match()

    # Serialize the best_match list properly, including ObjectId handling
    best_match_top_relevant_keys = map(lambda ele: {'type': ele['element_type'], 'name': ele['name'], 'location': ele['file_location']} ,best_match)

    # best_match_top_relevant_keys = map(lambda ele: {'type': ele['type'], 'name': ele.get("additional_data", {}).get("name", ""),
    #                                                 'location': ele['file_location'], 'metdata': ele['metadata']} ,best_match)
    
    best_match_serialized = json.loads(json_util.dumps(best_match_top_relevant_keys))
    print("Best Match Elements:", json.dumps(best_match_serialized, indent=4))
    print("Best Match Elements Length:", len(best_match_serialized))
    print("Code Graph Expected Output:", name_to_path_tuple_generator(best_match_serialized))

if __name__ == "__main__":
    main()

# From 'AI-TC-s-Generator/data-pre' we can run the script with the following command: 'python -m meta_data.main'
# Steps to Access MongoDB Through SSH Tunneling: "ssh -L 27018:localhost:27017 user@VM_IP" (ssh -L 27018:localhost:27017 cloud-user@10.46.249.22)
# Connect to MongoDB Using MongoDB Compass: "mongodb://localhost:27018/
# Optional: Keep the Tunnel Open: "ssh -f -N -L 27018:localhost:27017 user@VM_IP" (-f runs SSH in the background, -N tells SSH not to execute commands on the remote host)