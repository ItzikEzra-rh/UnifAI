import os
from tree_sitter import Language, Parser

# Define paths
repo_dir = '/home/instruct/tree-sitter-robot'
so_file = os.path.join(repo_dir, 'robot.so')

# Load the language
ROBOT_LANGUAGE = Language(so_file, 'robot')

def parse_source_code(language, source_code):
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(source_code, "utf8"))
    return tree

def extract_test_cases(tree):
    test_cases = []
    cursor = tree.walk()

    def traverse(node):
        if node.type == 'section_header' and node.text.decode('utf8') == '*** Test Cases ***':
            while node.next_sibling and node.next_sibling.type != 'section_header':
                node = node.next_sibling
                if node.type == 'test_case':
                    test_case = {
                        'name': node.child_by_field_name('name').text.decode('utf8'),
                        'body': node.child_by_field_name('body').text.decode('utf8')
                    }
                    test_cases.append(test_case)
        for child in node.children:
            traverse(child)

    traverse(cursor.node)
    return test_cases

def combine_test_cases(test_cases):
    combined_tests = []
    for i in range(len(test_cases)):
        for j in range(i + 1, len(test_cases)):
            new_test = f"*** Test Cases ***\nCombined Test {i}_{j}\n"
            new_test += f"    {test_cases[i]['name']} Body:\n    {test_cases[i]['body']}\n"
            new_test += f"    {test_cases[j]['name']} Body:\n    {test_cases[j]['body']}\n"
            combined_tests.append(new_test)
    return combined_tests

def generate_tests_for_language(source_code):
    tree = parse_source_code(ROBOT_LANGUAGE, source_code)
    test_cases = extract_test_cases(tree)
    return combine_test_cases(test_cases)

# Example usage
source_code_robot = """
*** Settings ***
Documentation  Cleanup all robot-* named images

Test Timeout    15 min

Resource    ../../resource/config.robot
Resource    ../../resource/setup.robot
Resource    ../../resource/image.robot

Suite Setup     setup.suite_setup
Suite Teardown  setup.suite_teardown

*** Test Cases ***

precase_setup
    [Documentation]  Run Precase setup - ncs rest api login, get cluster name, setup ncs cli config and login.
    setup.precase_setup
    Run Keyword If  "${S_IS_BAREMETAL_INSTALLATION}"=="${TRUE}"  setup.setup_ncs_centralsite_name
    Run Keyword If  "${S_IS_BAREMETAL_INSTALLATION}"=="${TRUE}"  internal_is_central

check_case_requirements
    internal_check_prereqs

precase_ncs_login
    setup.set_ncs_endpoint
    setup.login_ncs_endpoint

delete_podman_images
    [Documentation]  Delete podman images
    image.delete_podman_images

*** Keywords ***
internal_check_prereqs
    ${is_baremetal_installation}=  config.is_baremetal_installation
    Set Suite Variable  ${S_IS_BAREMETAL_INSTALLATION}  ${is_baremetal_installation}

internal_is_central
    [Documentation]  Check if central setup
    ${mode}=  config.ncs_config_mode
    ${central}=  Run Keyword If  "${mode}"=="config5"  Set Variable  ${TRUE}
    ...  ELSE  Set Variable  ${FALSE}
    Set Suite Variable  ${S_CENTRAL}  ${central}
"""
tree = parse_source_code(ROBOT_LANGUAGE, source_code_robot)
print(tree)