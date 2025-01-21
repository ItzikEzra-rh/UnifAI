import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.robot_parser import RobotParser
from components.tree_sitter_parser import TreeSitterParser

GO_FOLDER = '/home/cloud-user/Projects/tag-integration-with-migration-planner/migration-planner'
AGENT_NAME = '(DEEP_CODE)'
GO_PROJECT_NAME = 'migration-planner'
GO_SUFFIXES = [".go"]

def write_to_file(my_list, filename="TC's_mapping_list.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

def get_file_paths_with_suffixes(folder_path, suffixes):
    file_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Check if the file matches the pattern 'STRING_TXT.robot/STRING_TXT.resource'
            if any(file.endswith(suffix) for suffix in suffixes):
                # Construct the full file path
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    return file_paths

def extract_unique_words(paths):
    """
    Extracts a set of unique words from a list of paths.
    Includes directory names and file names without extensions.
    Only includes file names with `.go` suffix.

    Args:
        paths (list): List of file paths as strings.

    Returns:
        set: Set of unique words.
    """
    unique_words = set()

    for path in paths:
        # Split the path into components
        components = path.split(os.sep)
        for component in components:
            # Check if it's a file with an extension
            if "." in component:
                name, extension = os.path.splitext(component)
                # Include only if the extension is .go
                if extension == ".go":
                    unique_words.add(name)
            else:
                # Add directory names
                unique_words.add(component)
    
    return unique_words

def parser_error_counter(go_files):
    # Initialize a counter and a list for paths
    error_count = 0
    error_paths = []

    # Loop through all the files
    for path in go_files:
        tree_sitter_parser = TreeSitterParser.create_parser(file_path=path)
        node, _ = tree_sitter_parser.get_root_node()
        
        # Check if the node contains an error
        if tree_sitter_parser.is_error_node(node):
            error_count += 1
            error_paths.append(path)

    # Print the total count and the paths with errors
    print(f"Total number of files with errors: {error_count}")
    print("Paths with errors:")
    for error_path in error_paths:
        print(error_path)

go_files = get_file_paths_with_suffixes(GO_FOLDER, GO_SUFFIXES)
print(f'GO_FILES len: {len(go_files)}')

#########################################################################################################

project_file_names_mapping = {}
project_files_mapping = []
counter = 0

for path in go_files:
    print(f"Current path:{path}")
    realtive_file_path = path.replace(f"{GO_FOLDER}/", "", 1)
    tree_sitter_parser = TreeSitterParser.create_parser(file_path=path, realtive_path=realtive_file_path, project_name=GO_PROJECT_NAME)
    project_entire_file_mapping = [tree_sitter_parser.enitre_file_parsing(project_file_names_mapping)]
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
write_to_file(json_formatted_str, filename=f'{GO_PROJECT_NAME}_Mapping {AGENT_NAME}.json')
print(f"Number Of Parsed Files: {counter}")

# print(f"Parsed Json: \n {json_formatted_str}")

# Example usage
# realtive_paths = [path.replace("/home/cloud-user/Projects/tag-integration-with-cnv/kubevirt/", "", 1) for path in go_files]
# result = extract_unique_words(realtive_paths)