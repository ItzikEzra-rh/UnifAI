#########################################################################################################
# from tree_sitter_languages import get_language, get_parser
# language = get_language('python')
# parser = get_parser('python')
#########################################################################################################

"""
For parsing purposes we are using library called tree-sitter that parsing ROBOT files as AST structures.
Under tree-sitter official webpage currently there is no support for robot framework.
There is a library called tree-sitter-robot which add robot parsing capabilities to tree-sitter.
Currently the grammar which written as part of the tree-sitter-robot is not fully synched with the latest robot official version,
therefore there are some adjustments that need to be added to the grammar section for proper support for robot framwork.
E.G. https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#if-else-syntax 'Inline IF' need to be supported.

Please follow the following steps to intergate with tree-sitter on your working environment:
    - pip install -U tree-sitter==0.21.3
    - nvm use 16
    - tree-sitter init-config
        {
        "parser-directories": ["{WORKING_DIR}/{TREE_SITTER_FOLDER}"] (robot.so file should be placed here)
        }

    tree-sitter parse <robot_file_path>

Please follow the following steps to intergate with tree-sitter-playground on your working environment:
    - git clone https://github.com/Hubro/tree-sitter-robot.git
    - cd {WORKING_DIR}/tree-sitter-robot
    - nvm use 16
    - tree-sitter generate
    - tree-sitter build --wasm (required only for the tree-sitter playground CLI commands)
    - cd {WORKING_DIR}/{TREE_SITTER_FOLDER}
    - tree-sitter playground --grammar-path tree-sitter-robot/
"""

import os
import json
from components.robot_parser import RobotParser
from robot_parsing_appendix import robot_test_example, robot_test_second_example

robot_parser = RobotParser()

def write_to_file(my_list, filename="TC's_mapping_list.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

#########################################################################################################

# combined_test = robot_parser.combine_robot_tests(robot_test_example, robot_test_second_example)

# # Output the combined test
# print(combined_test)

#########################################################################################################

# def process_test_cases(test_case_list, folder_path):
#     all_outputs = []
#     test_cases_combination = []
#     error_counter = 0
#     for idx, test_combination in enumerate(test_case_list):
#         for _tuple in test_combination:
#             try:
#                 test_case_name, file_name = _tuple
#                 file_path = os.path.join(folder_path, file_name + '.robot')
#                 robot_parser = RobotParser(file_path=file_path)
#                 # Call the export_test_case function with the test case name and file path
#                 output = robot_parser.test_cases_parser(specific_test_case_name=test_case_name)
#                 if output:
#                     test_cases_combination.append(output[0])
#             except Exception as e:
#                 error_counter += 1
#                 print("Error: {0} {1} {2}".format(idx, error_counter, e))
#                 pass
            
#         all_outputs.append(test_cases_combination) 
#         test_cases_combination = []

#     return all_outputs

# def combine_all_robot_tests(test_list, robot_parser, idx):
#     # Initialize with the first test
#     combined_test = test_list[0]

#     # Iteratively combine with the next tests
#     for test in test_list[1:]:
#         combined_test = robot_parser.combine_robot_tests(combined_test, test)

#     return {idx: combined_test}

# folder_path = '/home/cloud-user/Projects/Robot-POC-InstructLab/24.0'
# test_cases_combination_list = []
# combined_result = {}

# with open('/home/cloud-user/Projects/playGround/tree-sitter-playground/scripts/combination_test_cases_res_mini.json', 'rb') as file:
#     content = file.read()
#     test_cases_combination_list = json.loads(content)
    
# all_outputs = process_test_cases(test_cases_combination_list, folder_path)
# write_to_file(json.dumps(all_outputs), filename='TCs_combination_all_outputs.txt')

# with open('/home/cloud-user/Projects/playGround/tree-sitter-playground/TCs_combination_all_outputs.txt', 'rb') as file:
#     content = file.read()
#     all_outputs = json.loads(content)

# for idx, combination in enumerate(all_outputs):
#     if combination:
#         combined_result.update(combine_all_robot_tests(combination, robot_parser, idx))

# print(combined_result[0])
# write_to_file(json.dumps(combined_result), filename='TCs_combination_list.txt')

#########################################################################################################

# parsed_sections = robot_parser.robot_sections_parser()
# for section, items in parsed_sections.items():
#     print(f"\n{section}:")
#     for item in items:
#         print(f"  - {item}")

# TODO: INPUT: ["tc_zabbix_server_status", "8103_Zabbix_server_is_running_in_all_manage_nodes"], OUTPUT: Single elemnet parsing for 1 TC's doesn't include
# TODO: (Resource ../../resource/zabix.robot) as expected

# test_cases = robot_parser.test_cases_parser()
# print("\nTest Cases:\n")
# for test_case in test_cases:
#     print(f"{test_case}\n")
#     print('------------------------------------------------------------------------------------------')

# robot_parser.parse_and_print()

#########################################################################################################

# robot_folder = '/home/cloud-user/Projects/Robot-POC-InstructLab/24.0'
# robot_files = get_robot_file_paths_with_suffixes(robot_folder, 'robot')
# robot_file_test_cases_mapping = {}

# for path in robot_files:
#     robot_parser = RobotParser(file_path=path)
#     test_cases_name_list = robot_parser.get_test_cases_name_list()
#     robot_file_test_cases_mapping.update(test_cases_name_list)

# print("\nRobot Files // Test Cases Mapping List:\n")
# print(robot_file_test_cases_mapping)
# write_to_file(json.dumps(robot_file_test_cases_mapping))

#########################################################################################################

def get_robot_file_paths_with_suffixes(folder_path, suffixes):
    robot_file_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Check if the file matches the pattern 'STRING_TXT.robot/STRING_TXT.resource'
            if any(file.endswith(suffix) for suffix in suffixes):
                # Construct the full file path
                full_path = os.path.join(root, file)
                robot_file_paths.append(full_path)

    return robot_file_paths

def add_to_dict(file_name, objects_list, target_dict):
    """
    Adds objects to the target_dict where the key is the 'name' from the object.
    The value is a dictionary with two keys:
      - 'file_names': a list of file names
      - 'documentation': a list of documentation strings.
    
    If the 'name' already exists, append the file_name and documentation to the respective lists.
    """
    for obj in objects_list:
        name = obj['name']
        documentation = obj['documentation']

        if name not in target_dict:
            # Add a new entry with 'file_names' and 'documentation' lists
            target_dict[name] = {
                'file_names': [file_name],
                'documentation': [documentation]
            }
        else:
            # Append to existing lists
            target_dict[name]['file_names'].append(file_name)
            target_dict[name]['documentation'].append(documentation)

def count_objects_with_multiple_files(target_dict):
    """
    Counts the number of objects in the dictionary that have more than one element in 'file_names'.
    """
    count = 0
    for key, value in target_dict.items():
        if len(value['file_names']) > 1:
            # print(f"{key}: {value}")
            count += 1
    return count

def print_objects(target_dict):
    """
    Prints each object from the dictionary with its 'name', 'file_names', and 'documentation'.
    """
    for key, value in target_dict.items():
        print(f"Name: {key}")
        print(f"File Names: {value['file_names']}")
        print(f"Documentation: {value['documentation']}")
        print("-" * 40)

robot_folder = '/home/cloud-user/Projects/ods-ci'
suffixes = [".resource", ".robot"]  # List of suffixes to search for
robot_files = get_robot_file_paths_with_suffixes(robot_folder, suffixes)
robot_file_keywords_mapping = {}
robot_file_libraries_mapping = {}
robot_file_names_mapping = {}

# for path in robot_files:
#     robot_parser = RobotParser(file_path=path)
#     file_name, keywords_name_list = robot_parser.get_keywords_name_list()
#     realtive_file_name = path.replace("/home/cloud-user/Projects/ods-ci/", "", 1)
#     last_string_in_file_name = realtive_file_name.split('/')[-1]

#     # if (last_string_in_file_name in robot_file_names_mapping):
#     #     print(f'Same suffix file name, already exist: {last_string_in_file_name}')
    
#     robot_file_names_mapping.update({
#         f'{last_string_in_file_name}': realtive_file_name
#     })
#     add_to_dict(realtive_file_name, keywords_name_list, robot_file_keywords_mapping)

#     # Get the current library dictionary
#     current_libraries = robot_parser.get_libraries_name_list()

#     # Merge current_libraries into robot_file_libraries_mapping
#     robot_file_libraries_mapping.update(current_libraries)

# multiple_files_count = count_objects_with_multiple_files(robot_file_keywords_mapping)
# print(f"Number of objects with more than 1 file: {multiple_files_count}")

# print("\nRobot Files // Keywords Mapping List:\n")
# print_objects(robot_file_keywords_mapping)
# write_to_file(json.dumps(robot_file_keywords_mapping), filename="RHOAI_Keyword's_mapping_list.txt")

#########################################################################################################
# The following is an example of the JSON STRUCTURE we want to have within the usage of our parser
"""
{
    "code": "TEST_CASE_CODE",
    "dependencies": {settings: "setting the test uses",
                    varaibles: "vars its uses"},
    "imports_file_locations": {../../fsdfs/fsdf.recource:  ocdi/fsdfs/fsdf.recource}
    "calls": [KEYWORD_NAMES],
    "file_location": "Relative path",
    "type": "TestCase"
}

Another optional types:
    "type": "Resource" (most not contain test cases)
    "type: "Test" (most contain test cases)

KEYWORD_NAMES --> list of objects, each object is:
    {keyword: {"file_location": "Relative path", "documentation": KEYWORD_documentation}}
"""

robot_folder = '/home/cloud-user/Projects/ods-ci'
suffixes = [".robot"]  # List of suffixes to search for
robot_files = get_robot_file_paths_with_suffixes(robot_folder, suffixes)

# robot_file_internal_functions_mapping = {}
# for path in robot_files:
#     robot_parser = RobotParser(file_path=path)
#     robot_file_internal_functions_mapping = robot_parser.get_full_internal_calls_list(robot_file_keywords_mapping, robot_file_libraries_mapping)

#     test_cases_list = robot_parser.extract_test_cases()
#     realtive_file_name = path.replace("/home/cloud-user/Projects/ods-ci/", "", 1)
#     add_to_dict(realtive_file_name, test_cases_list, robot_file_internal_functions_mapping)

# Initialize a counter and a list for paths
error_count = 0
error_paths = []

# robot_files=["/home/cloud-user/Projects/ods-ci/ods_ci/tasks/Resources/RHODS_OLM/uninstall/uninstall.robot"]
# robot_files = ["/home/cloud-user/Projects/ods-ci/ods_ci/tasks/Tasks/provision_self_managed_cluster.robot"]
# robot_files = ["/home/cloud-user/Projects/ods-ci/ods_ci/tasks/Resources/Provisioning/Hive/provision.robot"]
# Loop through the robot files
for path in robot_files:
    robot_parser = RobotParser(file_path=path)
    # robot_parser.add_end_to_if_statements(robot_parser.file_path)    
    node, _ = robot_parser.get_root_node()
    
    # Check if the node contains an error
    if robot_parser.is_error_node(node):
        error_count += 1
        error_paths.append(path)

# Print the total count and the paths with errors
print(f"Total number of files with errors: {error_count}")
print("Paths with errors:")
for error_path in error_paths:
    print(error_path)

# full_file_path = "/home/cloud-user/Projects/ods-ci/ods_ci/tests/Tests/0100__platform/0101__deploy/0101__installation/0101__post_install.robot"
# full_file_path = "/home/cloud-user/Projects/ods-ci/ods_ci/tests/Tests/0100__platform/0101__deploy/0101__installation/0104__prometheus.robot"
# full_file_path = "/home/cloud-user/Projects/ods-ci/ods_ci/tasks/Resources/RHODS_OLM/install/oc_install.robot"
full_file_path = "/home/cloud-user/Projects/ods-ci/ods_ci/tasks/Resources/Provisioning/Hive/deprovision.robot"

# realtive_file_path = full_file_path.replace("/home/cloud-user/Projects/ods-ci/", "", 1)
# robot_parser = RobotParser(file_path=full_file_path, realtive_path=realtive_file_path)
# robot_parser.get_root_node()
# robot_file_internal_functions_mapping = robot_parser.get_full_internal_calls_list(robot_file_keywords_mapping, robot_file_libraries_mapping)
# json_formatted_str = json.dumps(robot_file_internal_functions_mapping, indent=2)

robot_files_internal_functions_mapping = []
counter = 0

# for path in robot_files:
#     realtive_file_path = path.replace("/home/cloud-user/Projects/ods-ci/", "", 1)
#     robot_parser = RobotParser(file_path=path, realtive_path=realtive_file_path)
#     robot_entire_file_mapping = robot_parser.enitre_file_parsing(robot_file_names_mapping)    
#     robot_file_internal_functions_mapping = robot_parser.get_full_internal_calls_list(robot_file_keywords_mapping, robot_file_libraries_mapping)
#     robot_file_mapping = robot_entire_file_mapping + robot_file_internal_functions_mapping
#     counter+= len(robot_file_mapping)
#     try:
#         robot_files_internal_functions_mapping.append(robot_file_mapping)
#     except (TypeError, ValueError) as e:
#         print(f"Failed to update with: {e}")

# json_formatted_str = json.dumps(robot_files_internal_functions_mapping, indent=2)
# write_to_file(json_formatted_str, filename='RHOAI_Files_Mapping.txt')
print(counter)