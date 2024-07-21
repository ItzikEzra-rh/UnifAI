from .openstack_cli import Cli
from config.configParams import config_params
import json


def get_servers_ip_mapping():
    """
    get server list as json, return parsed json with server name as key and ip as value
    :return:
    """
    result = {}
    cli = Cli(source_file=config_params.CBIS_STACKRC)
    rc, stdout = cli.server_list()
    data = json.loads(stdout)
    for server_info in data:
        server_name = server_info['Name'].strip()
        internal_ip = server_info['Networks']['ctlplane'][0].strip()
        result[server_name] = internal_ip
    return result