import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.tree_sitter_parser import TreeSitterParser

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

type_script_folder = '/home/cloud-user/Projects/tag-integration-with-mta/tackle-ui-tests'
type_script_suffixes = [".ts", ".tsx"]
type_script_files = get_file_paths_with_suffixes(type_script_folder, type_script_suffixes)
print(f'TS_FILES len: {len(type_script_files)}')

#########################################################################################################

# Initialize a counter and a list for paths
error_count = 0
error_paths = []

# # Loop through all the files
# for path in type_script_files:
#     tree_sitter_parser = TreeSitterParser.create_parser(file_path=path)
#     node, _ = tree_sitter_parser.get_root_node()
    
#     # Check if the node contains an error
#     if tree_sitter_parser.is_error_node(node):
#         error_count += 1
#         error_paths.append(path)

# # Print the total count and the paths with errors
# print(f"Total number of files with errors: {error_count}")
# print("Paths with errors:")
# for error_path in error_paths:
#     print(error_path)

project_files_mapping = []
counter = 0

for path in type_script_files:
    realtive_file_path = path.replace("/home/cloud-user/Projects/tag-integration-with-mta/tackle-ui-tests/", "", 1)
    print(f"Current path:{path}")
    print(f"Realtive path:{realtive_file_path}")
    tree_sitter_parser = TreeSitterParser.create_parser(file_path=path, realtive_path=realtive_file_path, project_name="tackle-ui-tests")
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

print(f"Number of files:" + str(counter))
json_formatted_str = json.dumps(project_files_mapping, indent=2)
write_to_file(json_formatted_str, filename='MTA_tests.json')
# print(json_formatted_str)