from rag.be_utils.db.db import mongo, Collections, db
import sys
import json
import os

from rag.meta_data.helpers.meta_data_project_expander import MetaDataProjectExpander

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

# @mongo
# def insert_new_prompt(model_id, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name):
#     """inserting new llm prompt response to the database

#     :param str model_id:
#     :param str training_name:
#     :param str prompt_entire_text: 
#     :param str prompt_user_latest_text: 
#     :param str prompt_llm_latest_text: 
#     :param str prompt_name:
#     :return:
#     """
#     # Generate a unique identifier
#     unique_id = str(uuid.uuid4())

#     result = Collections.by_name('prompts').insert_one({'modelId': model_id,
#                                                         'uniqueId': unique_id,
#                                                         'trainingName': training_name,
#                                                         'promptText': prompt_entire_text,
#                                                         'promptUserLatestText': prompt_user_latest_text,
#                                                         'promptLLMLatestText': prompt_llm_latest_text,
#                                                         'promptName': prompt_name,
#                                                         'comment': ''})
#     return result

