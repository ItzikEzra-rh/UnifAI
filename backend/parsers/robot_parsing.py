#########################################################################################################
# from tree_sitter_languages import get_language, get_parser
# language = get_language('python')
# parser = get_parser('python')
#########################################################################################################

import os
import json
from components.robot_parser import RobotParser

# robot_parser = RobotParser()

# parsed_sections = robot_parser.robot_sections_parser()
# for section, items in parsed_sections.items():
#     print(f"\n{section}:")
#     for item in items:
#         print(f"  - {item}")

# test_cases = robot_parser.test_cases_parser()
# print("\nTest Cases:\n")
# for test_case in test_cases:
#     print(f"{test_case}\n")
#     print('------------------------------------------------------------------------------------------')

# robot_parser.parse_and_print()

#########################################################################################################

def get_robot_file_paths(folder_path):
    robot_file_paths = []

    # Walk through the directory
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Check if the file matches the pattern 'STRING_TXT.robot'
            if file.endswith(".robot"):
                # Construct the full file path
                full_path = os.path.join(root, file)
                robot_file_paths.append(full_path)

    return robot_file_paths

def write_to_file(my_list, filename="TC's_mapping_list.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

robot_folder = '/home/cloud-user/Projects/Robot-POC-InstructLab/24.0'
robot_files = get_robot_file_paths(robot_folder)
robot_file_test_cases_mapping = {}

for path in robot_files:
    robot_parser = RobotParser(file_path=path)
    test_cases_name_list = robot_parser.get_test_cases_name_list()
    robot_file_test_cases_mapping.update(test_cases_name_list)

print("\nRobot Files // Test Cases Mapping List:\n")
print(robot_file_test_cases_mapping)
write_to_file(json.dumps(robot_file_test_cases_mapping))