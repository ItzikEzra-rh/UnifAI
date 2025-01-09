from rag.be_utils.db.db import mongo, Collections, db
import sys
import json
import os
import re
from bson import json_util

from rag.meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander
from rag.meta_data.helpers.meta_data_retriever import MetaDataRetriever
from rag.meta_data.helpers.meta_data_query_expander import MetaDataQueryExpander

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

def parsed_elements_metadata_expansion(parsed_elements_location, project_name, project_repo_path, naming_mapping, built_in_keys, exclude_types, project_programming_languages):
    # Path to the JSON file containing parsed objects
    parsed_elements = read_file(parsed_elements_location)

    project_meta_expander = MetaDataProjectExpander(
        parsed_elements=parsed_elements,
        project_name=project_name,
        project_repo_path=project_repo_path,
        naming_mapping=naming_mapping,
        built_in_keys=built_in_keys,
        exclude_types=exclude_types,
        project_programming_languages=project_programming_languages
    )

    # Add metadata to each parsed element & Add the entire elements to the DB
    project_meta_expander.add_metadata()
    project_meta_expander.add_to_db()

def query_meta_data_retrieval(text, project_name, model_name, model_id):
    query_meta_expander = MetaDataQueryExpander(
        query=text,
        project_name=project_name,
        model_name=model_name,
        model_id=model_id
    )

    # Extract metadata for the query
    query_metadata = query_meta_expander.extract_metadata()

    meta_data_retreiver = MetaDataRetriever(query_metadata=query_metadata)
    best_match = meta_data_retreiver.best_match()

    # Serialize the best_match list properly, including ObjectId handling
    best_match_top_relevant_keys = map(lambda ele: {'type': ele['element_type'], 'name': ele['name'], 'location': ele['file_location']} ,best_match)    
    best_match_serialized = json.loads(json_util.dumps(best_match_top_relevant_keys))
    return name_to_path_tuple_generator(best_match_serialized)