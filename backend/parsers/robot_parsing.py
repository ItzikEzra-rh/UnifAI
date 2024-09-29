#########################################################################################################
# from tree_sitter_languages import get_language, get_parser
# language = get_language('python')
# parser = get_parser('python')
#########################################################################################################

import os
import json
from components.robot_parser import RobotParser

def write_to_file(my_list, filename="TC's_mapping_list.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

robot_parser = RobotParser()

#########################################################################################################

robot_test_a = """
*** Settings ***
Documentation    6003_Scale_in_out_worker_node_after_failed_scale_out.robot. Same worker node used with same IPMI address.
...              Validation and check on each major step before and after each scale operation.
...              Security Hardening - this test running full SH after the final Scale-out operation.

Force Tags  production

Test Timeout    240 min

Resource    ../../resource/setup.robot
Resource    ../../resource/config.robot


Library     Collections
Library     String
Library     DateTime

Suite Setup     setup.suite_setup
Suite Teardown  setup.suite_teardown


*** Variables ***
${T_PING_DOMAIN_A}              jiradc2.ext.net.nokia.com  # default address 1 to be pinged  # Give new address as a same name parameter, if this is not pingable from active master and centralsite manager #jiradc2.ext.net.nokia.com
${T_PING_DOMAIN_B}              www.nokia.com              # default address 2 to be pinged  # Give new address as a same name parameter, if this is not pingable from active master and centralsite manager #testmanager.nsn-net.net

# Due to NCSTA-1612 - file 1_defaultrouting.yaml is used for this test from path 24/testcase_config_files/ZTS/egress/
${C_EGRESS_FILES_PATH}          24/testcase_config_files/ZTS/egress/
${C_DEFAULT_ROUTING}            1_defaultrouting.yaml

*** Test Cases ***
precase_setup
    [Documentation]  Run Precase setup - ncs rest api login, get cluster name, setup ncs cli config and login.
    Log  S_IS_BAREMETAL_INSTALLATION: ${C_DEFAULT_ROUTING}
    setup.precase_setup
    # optional - ADD OPTIONAL precase kws here
    internal_case_nir_nothing

nir_debug_test_case
    [Documentation]  Nir Debug - just casual text.
    setup.precase_setup
    Log  S_IS_BAREMETAL_INSTALLATION: ${C_DEFAULT_ROUTING}
    internal_case_nir_debug_extra

*** Keywords ***

internal_case_baremetal_check
    Log  S_IS_BAREMETAL_INSTALLATION: ${T_PING_DOMAIN_B}
    Log  S_IS_BAREMETAL_INSTALLATION: ${C_DEFAULT_ROUTING}
    setup.precase_setup

internal_case_nir_debug
    Log  NIR_DEBUG: ${S_IS_BAREMETAL_INSTALLATION}
    internal_case_nir_debug_extra

internal_case_nir_debug_extra
    Log  NIR_DEBUG_EXTRA: ${T_PING_DOMAIN_A}
    internal_case_baremetal_check
    config.installed_ncs_sw_package
    ${match}=  String.Get Regexp Matches  ${std_out}   ${S_SCALED_NODE_NAME}

internal_case_nir_nothing
    [Documentation]  Nir Debug - just casual text.
"""

robot_test_b = """
*** Settings ***
Documentation    scale-in worker node and after scale out the same worker node using it IPMI address.
...              validation and check on each major step before and after each scale oparation.
...              Security Hardening - this test running full SH after the Scale-out operation.
...              Optionally DNS IP change operations are done/checked during the scale out/in operation.\\n
...              If the dns change operation is to be part of the scale in/out operation,\\n
...              then the user should add the dns test parameters with the correct values.\\n
...              Test DNS IPs must not be the same for Central and Cluster.\\n
...              Both test parameters are needed for config5 and for the other configs only parameter for cluster: T_EXT_DNS_IP_CENTRAL:<ip>'and 'T_EXT_DNS_IP_CLUSTER:<ip>'\\n
...              DNS IP operation&check is automatically Skipped, if test parameters T_EXT_DNS_IP_x are missing, parameter values are missing,values are wrongly given,\\n
...              values are same for central and cluster\\n
...              NOTE! It is recommended to use separate test parameters for the domain addresses (fqdn), which have been beforehand confirmed to be pingable in the environment.
...              Default addresses, see *** Variables ***, may not be working in every setup.\\n
...                   - parameters to be optionally used: T_PING_DOMAIN_A & T_PING_DOMAIN_B\\n
...
...              Optionally NTP IP change operations are done/checked during the scale out/in operation.\\n
...              If the ntp change operation is to be part of the scale in/out operation,\\n
...              then the user should add the ntp test parameters with the correct values.\\n
...              Test parameter needed as a flag:-v T_EXT_NTP_IP:<ip>\\n
...              NTP IP operation & check is automatically skipped, if test parameter is missing, parameter value is missing, value is wrongly given\\n


Force Tags  production

Test Timeout    180 min

Resource    ../../resource/config.robot
Resource    ../../resource/ssh.robot
Resource    ../../resource/middleware.robot
Resource    ../../resource/namespace.robot
Resource    ../../resource/node.robot
Resource    ../../resource/setup.robot
Resource    ../../resource/ncsManagerOperations.robot
Resource    ../../resource/ncsManagerSecurity.robot
Resource    ../../resource/scale.robot
Resource    ../../resource/ipmi.robot
Resource    ../../resource/ping.robot
Resource    ../../resource/check.robot
Resource    ../../infra/ncmRestApi.robot
Resource    ../../infra/ncsManagerRestApi.robot
Resource    ../../infra/k8sRestApi.robot
Resource    ../../suites/helpers/validate_var_log_partition.robot


Library     Collections
Library     String

Suite Setup     setup.suite_setup
Suite Teardown  setup.suite_teardown



*** Variables ***
${T_PING_DOMAIN_A}                             jiradc2.ext.net.nokia.com  # default address 1 to be pinged  # Give new address as a same name parameter, if this is not pingable from active master and centralsite manager #jiradc2.ext.net.nokia.com
${T_PING_DOMAIN_B}                             www.nokia.com              # default address 2 to be pinged  # Give new address as a same name parameter, if this is not pingable from active master and centralsite manager #testmanager.nsn-net.net

# Due to NCSTA-1612 - file 1_defaultrouting.yaml is used for this test from path 24/testcase_config_files/ZTS/egress/
${C_EGRESS_FILES_PATH}          24/testcase_config_files/ZTS/egress/
${C_DEFAULT_ROUTING}            1_defaultrouting.yaml

*** Test Cases ***

get_Host_Group
    [Documentation]  getting the Host_Group
    [Tags]  Test1  Test20
    internal_check_if_case_is_valid
    ${host_group_data}=  ncsManagerOperations.get_host_group_operations_bm_data
    ${host_group_data1}=  Get Value From Json   ${host_group_data}  $.content
    Log  ${host_group_data1}   formatter=repr

    ${get_hostgroups_dictionary}=  Get Value From Json   ${host_group_data1}[0]  $.hostgroups
    Set Suite Variable    ${S_HOST_GROUPS_JSON_ORIG}    ${get_hostgroups_dictionary}[0]
    Log  ${get_hostgroups_dictionary}[0]
#    ${keys}=  Collections. Get Dictionary Keys  ${get_hostgroups_dictionary}[0]
#    FOR  ${i}  IN   @{keys}

create_json_payload_for_scale_in
    [Documentation]  construct the json payload for scale in and add to a suite Variable.
    [Tags]  skip
    internal_check_if_case_is_valid
    scale.create_json_payload_for_scale_in   ${S_SCALED_NODE_NAME}  ${S_HOST_GROUP_FOR_JSON}
"""

# combined_test = robot_parser.combine_robot_tests(robot_test_a, robot_test_b)

# # Output the combined test
# print(combined_test)

#########################################################################################################

# test_cases_combination_list = [('precase_setup', '2022_reboot_all_node_types_concurrently'),
# ('precase_cluster_status', '2022_reboot_all_node_types_concurrently'),
# ('check_that_power_is_on_in_all_nodes', '2022_reboot_all_node_types_concurrently'),
# ('ping_nodes_before_reboot', '2022_reboot_all_node_types_concurrently'),
# ('restart_nodes', '2022_reboot_all_node_types_concurrently'),
# ('wait_until_nodes_ping', '2022_reboot_all_node_types_concurrently'),
# ('precase_setup', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('precase_cluster_status', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('check_test_case_parameter', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('copy_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('create_one_container', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('create_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('check_tenants', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('set_passwords', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('tenant_user_login', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('create_images_and_upload_to_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('regain_ncm_rest_api_login_credentials', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('check_tenant_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('delete_created_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('delete_container', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('delete_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('postcase_cleanup', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
# ('postcase_cluster_status', '3035_Verify_X_amount_of_image_uploads_in_one_tenant')]


def process_test_cases(test_case_list, folder_path):
    all_outputs = []
    test_cases_combination = []
    error_counter = 0
    for idx, test_combination in enumerate(test_case_list):
        for _tuple in test_combination:
            try:
                test_case_name, file_name = _tuple
                file_path = os.path.join(folder_path, file_name + '.robot')
                robot_parser = RobotParser(file_path=file_path)
                # Call the export_test_case function with the test case name and file path
                output = robot_parser.test_cases_parser(specific_test_case_name=test_case_name)
                if output:
                    test_cases_combination.append(output[0])
            except Exception as e:
                error_counter += 1
                print("Error: {0} {1} {2}".format(idx, error_counter, e))
                pass
            
        all_outputs.append(test_cases_combination) 
        test_cases_combination = []

    return all_outputs

def combine_all_robot_tests(test_list, robot_parser, idx):
    # Initialize with the first test
    combined_test = test_list[0]

    # Iteratively combine with the next tests
    for test in test_list[1:]:
        combined_test = robot_parser.combine_robot_tests(combined_test, test)

    return {idx: combined_test}

folder_path = '/home/cloud-user/Projects/Robot-POC-InstructLab/24.0'
test_cases_combination_list = []
combined_result = {}
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

# TODO: ["tc_zabbix_server_status", "8103_Zabbix_server_is_running_in_all_manage_nodes"] single parsing isn't include (Resource ../../resource/zabix.robot) as expected
# test_cases = robot_parser.test_cases_parser()
# print("\nTest Cases:\n")
# for test_case in test_cases:
#     print(f"{test_case}\n")
#     print('------------------------------------------------------------------------------------------')

# robot_parser.parse_and_print()

#########################################################################################################

# def get_robot_file_paths(folder_path):
#     robot_file_paths = []

#     # Walk through the directory
#     for root, dirs, files in os.walk(folder_path):
#         for file in files:
#             # Check if the file matches the pattern 'STRING_TXT.robot'
#             if file.endswith(".robot"):
#                 # Construct the full file path
#                 full_path = os.path.join(root, file)
#                 robot_file_paths.append(full_path)

#     return robot_file_paths

# robot_folder = '/home/cloud-user/Projects/Robot-POC-InstructLab/24.0'
# robot_files = get_robot_file_paths(robot_folder)
# robot_file_test_cases_mapping = {}

# for path in robot_files:
#     robot_parser = RobotParser(file_path=path)
#     test_cases_name_list = robot_parser.get_test_cases_name_list()
#     robot_file_test_cases_mapping.update(test_cases_name_list)

# print("\nRobot Files // Test Cases Mapping List:\n")
# print(robot_file_test_cases_mapping)
# write_to_file(json.dumps(robot_file_test_cases_mapping))

#########################################################################################################

def get_robot_file_paths(folder_path):
    robot_file_paths = []
    suffixes = [".resource"]  # List of suffixes to search for

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
robot_files = get_robot_file_paths(robot_folder)
robot_file_keywords_mapping = {}

for path in robot_files:
    robot_parser = RobotParser(file_path=path)
    file_name, keywords_name_list = robot_parser.get_keywords_name_list()
    add_to_dict(file_name, keywords_name_list, robot_file_keywords_mapping)

multiple_files_count = count_objects_with_multiple_files(robot_file_keywords_mapping)
print(f"Number of objects with more than 1 file: {multiple_files_count}")

print("\nRobot Files // Keywords Mapping List:\n")
print_objects(robot_file_keywords_mapping)
write_to_file(json.dumps(robot_file_keywords_mapping), filename="RHOAI_Keyword's_mapping_list.txt")