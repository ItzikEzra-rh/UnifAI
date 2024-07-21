from .openstack_api import OpenStackApi
from be_utils.utils import shell_exec
from be_utils.load_env import load_envbash
import json


class Cli(OpenStackApi):
    def __init__(self, source_file=None):
        super(Cli, self, ).__init__()
        if source_file:
            load_envbash(source_file, override=True)

    def stack_list(self, project_name=''):
        """
        Function that gets all the stacks in all projects
        :return:
        """
        rc, stdout = shell_exec(f'openstack stack list -f json')
        return rc, stdout

    def project_list(self):
        rc, stdout = shell_exec('openstack project list -f json')
        return rc, stdout

    def server_list(self, project='--all-projects'):
        rc, stdout = shell_exec(f'openstack server list {project} -f json')
        return rc, stdout

    def stack_resource_list(self, stack_id):
        rc, stdout = shell_exec('openstack stack resource list {} -f json'.format(stack_id))
        return rc, stdout

    def port_list(self, physical_resource_id):
        rc, stdout = shell_exec('openstack port list --device-id {} -f json'.format(physical_resource_id))
        if rc != 0:
            return []

        vm_network_info = json.loads(stdout)
        return vm_network_info

    def server_info(self, physical_resource_id):
        rc, stdout = shell_exec('openstack server show {} -f json'.format(physical_resource_id))
        return rc, stdout

    def baremetal_server_list(self):
        rc, stdout = shell_exec('openstack baremetal node list -f json')
        return rc, stdout

    def baremetal_server_show(self, uid):
        rc, stdout = shell_exec(f'openstack baremetal node show {uid} -f json')
        return rc, stdout

    def network_list(self):
        rc, stdout = shell_exec(f'openstack network list -f json')
        return rc, stdout

    def subnet_list(self):
        rc, stdout = shell_exec(f'openstack subnet list -f json')
        return rc, stdout

    def security_group_list(self):
        rc, stdout = shell_exec('openstack security group list -f json')
        return rc, stdout

    def security_group_show(self, uid):
        rc, stdout = shell_exec(f'openstack security group show {uid} -f json')
        return rc, stdout
