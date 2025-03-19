import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.tree_sitter_parser import TreeSitterParser

TYPE_SCRIPT_FOLDER = '/home/cloud-user/Projects/tag-integration-with-flight-control/flightctl-ui'
AGENT_NAME = '(DEEP_CODE)'
TYPE_SCRIPT_PROJECT_NAME = 'flightctl/flightctl-ui'
TYPE_SCRIPT_FILE_PROJECT_NAME = 'flightctl-ui'
TYPE_SCRIPT_SUFFIXES = [".ts", ".tsx", ".js"]

def write_to_file(my_list, filename="TC's_Mapping.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

def get_file_paths_with_suffixes(folder_path, suffixes):
    file_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if any(file.endswith(suffix) for suffix in suffixes):
                # Construct the full file path
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    return file_paths

type_script_files = get_file_paths_with_suffixes(TYPE_SCRIPT_FOLDER, TYPE_SCRIPT_SUFFIXES)
print(f'TS_FILES len: {len(type_script_files)}')
#########################################################################################################

project_files_mapping = []
counter = 0

for path in type_script_files:
    print(f"Current path:{path}")
    realtive_file_path = path.replace(f"{TYPE_SCRIPT_FOLDER}/", "", 1)
    tree_sitter_parser = TreeSitterParser.create_parser(file_path=path, realtive_path=realtive_file_path, project_name=TYPE_SCRIPT_PROJECT_NAME)
    project_entire_file_mapping = [tree_sitter_parser.enitre_file_parsing()]
    project_file_functions_mapping = tree_sitter_parser.functions_parsing()
    project_file_tests_mapping = tree_sitter_parser.test_parsing()
    project_entire_file_mapping.extend(project_file_functions_mapping)
    project_entire_file_mapping.extend(project_file_tests_mapping)
    counter+= 1
    try:
        project_files_mapping.extend(project_entire_file_mapping)
    except (TypeError, ValueError) as e:
        print(f"Failed to update with: {e}")

json_formatted_str = json.dumps(project_files_mapping, indent=2)
write_to_file(json_formatted_str, filename=f'{TYPE_SCRIPT_FILE_PROJECT_NAME}_Mapping{AGENT_NAME}.json')
print(f"Number Of Parsed Files: {counter}")

# print(json_formatted_str)