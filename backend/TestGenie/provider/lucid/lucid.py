import logging

from celery_app.tasks import fetch_resources_task
from be_utils.factory.platform_resources.resources import Resources
from be_utils.factory.network_topology.network_topology import NetworkTopology
from be_utils.factory.network.ping_test import PingTest
from be_utils.factory.network.fetch_interfaces import FetchInterfaces
from audit.ncs.audit_log_deprecated_api import AuditLogDeprecatedApi
from file_system.file_transfer import FileTransfer
from network.vlans_test import VlanTest
from config.configParams import config_params
import traceback
from config.configParams import ConfigParams
from collections import defaultdict
from file_system.list_dir import ListDir
from file_system.run_command import RunCommand
from config.file_system.config import Config as fileSystemConfig
from network.duplicate_ips import DuplicateIps
import os


def get_network_topology(node_name, instance_id, view):
    return NetworkTopology(node_name=node_name, instance_id=instance_id, view=view)()()


def get_resources():
    return Resources()().get_resources()


def get_network_functions_resources():
    resources = Resources()().get_virtual_resources_topology()
    convertor = Resources()().get_uuid_to_name_convertor()
    return {'resources': resources,
            'convertor': convertor}


def fetch_resources(background):
    if not background:
        try:
            Resources()().fetch()
            return True
        except Exception as e:
            logging.error(traceback.format_exc())
            return False
    else:
        task = fetch_resources_task.delay()
        return task.id


def fetch_resources_status(fetch_id):
    return fetch_resources_task.AsyncResult(fetch_id).state


def network_ping_connectivity_check(first_vr_uid, second_vr_uid, networks):
    return PingTest({
        "firstVrUid": first_vr_uid,
        "secondVrUid": second_vr_uid,
        "networks": networks
    })().run()


def shared_networks(vr1, vr2):
    return Resources()().get_shared_networks(vr1, vr2)


def network_interfaces_vlan_check(servers, mtu):
    return VlanTest(servers=servers, mtu=mtu).run()


def get_vlan_test_total_time():
    return int(config_params.NETWORK_VLAN_TEST_CAPTURE_TIME)


def get_configured_vlans():
    return Resources()().get_configured_vlans()


def metadata():
    return {
        'platform': os.environ.get('PLATFORM', ''),
        'bePort': ConfigParams.PRODUCTION_LUCID_BE_PORT,
        'uiPort': ConfigParams.PRODUCTION_LUCID_UI_PORT,
        'mongoSizeLimit': ConfigParams.MONGODB_SIZE_LIMITATION,
        'version': os.environ.get('VERSION', ''),
        'clusterName': os.environ.get('CLUSTER_NAME', ''),
    }


def fetch_interfaces_per_group(servers=None):
    res = defaultdict(set)
    servers_data = FetchInterfaces(servers=servers)().fetch()
    for uid, data in servers_data.items():
        group = data['group']
        res[group].update(data['interfaces'].keys())
        res['All'].update(data['interfaces'].keys())

    res = {group: list(interfaces) for group, interfaces in res.items()}
    return res


def fetch_interfaces(servers=None):
    return FetchInterfaces(servers=servers)().fetch()


def audit():
    return AuditLogDeprecatedApi().run()


def download_file(file_path, dest_host):
    return FileTransfer(file_path, dest_host).start()


def logs_config():
    return fileSystemConfig.get_logs_config()


def list_dir(path, host):
    return ListDir(path, dest_host=host).run()


def commands_config():
    return fileSystemConfig.get_commands_config()


def run_command(command, dest_host, command_id, is_stream, output_as_file, timeout, output_as_bytes):
    RunCommand.validator(command, command_id)
    command = RunCommand.update_command(command, command_id, timeout, output_as_bytes)
    return RunCommand(command=command,
                      dest_host=dest_host,
                      is_stream=is_stream,
                      output_as_file=output_as_file,
                      output_as_bytes=output_as_bytes).run()


def stop_command(command_id):
    command_obj = RunCommand.Running_commands.get(command_id, None)
    if not command_obj:
        err_msg = f'no command with ID {command_id} exist!'
        logging.error(err_msg)
        return err_msg
    return command_obj.stop()


def duplicate_ips():
    return DuplicateIps()()
