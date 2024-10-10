robot_test_example = """
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

robot_test_second_example = """
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

robot_test_cases_combination_list = [('precase_setup', '2022_reboot_all_node_types_concurrently'),
('precase_cluster_status', '2022_reboot_all_node_types_concurrently'),
('check_that_power_is_on_in_all_nodes', '2022_reboot_all_node_types_concurrently'),
('ping_nodes_before_reboot', '2022_reboot_all_node_types_concurrently'),
('restart_nodes', '2022_reboot_all_node_types_concurrently'),
('wait_until_nodes_ping', '2022_reboot_all_node_types_concurrently'),
('precase_setup', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('precase_cluster_status', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('check_test_case_parameter', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('copy_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('create_one_container', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('create_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('check_tenants', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('set_passwords', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('tenant_user_login', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('create_images_and_upload_to_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('regain_ncm_rest_api_login_credentials', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('check_tenant_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('delete_created_tenant', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('delete_container', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('delete_images', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('postcase_cleanup', '3035_Verify_X_amount_of_image_uploads_in_one_tenant'),
('postcase_cluster_status', '3035_Verify_X_amount_of_image_uploads_in_one_tenant')]