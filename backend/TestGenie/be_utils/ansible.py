# from ConfigParser import SafeConfigParser
# from config.configmanager import config
# from be_utils.utils import shell_exec
# import os
#
#
# class Ansible:
#     """
#     class that handle ansible env and inventory
#     """
#
#     def __init__(self, env_path, root_dir):
#         """
#         :param env_path: running env path
#         :param root_dir: root dir of the project
#         """
#         self.env_path = env_path
#         self.root_dir = root_dir
#         self.inventory_path = os.path.join(self.env_path, config.get('ansible', 'inventory_name'))
#         self.ansible_cfg = os.path.join(self.env_path, config.get('ansible', 'ansible_config_name'))
#
#
#     def __create_ansible_config(self):
#         """
#         ansible has default config file.
#         we copy it to the local running env so we can use our own edition
#         in this edition we change the retry in the ssh connection so it doesnt get stuck with unreachable hosts.
#         """
#         try:
#             utils.copy('/etc/ansible/ansible.cfg', self.ansible_cfg)
#             parser = SafeConfigParser()
#             parser.read(self.ansible_cfg)
#             parser.set('ssh_connection', 'retries', '0')
#             with open(self.ansible_cfg, 'w') as ansible_conf_file:
#                 parser.write(ansible_conf_file)
#         except Exception as e:
#             Exception('Problem in editing ansible cfg! {}'.format(str(e)))
#
#     def __create_host_file(self, node_list, user_input):
#         """
#         create ansible inventory file called hosts in the running env
#         its created accordance the node_list
#         It gets the ips of the nodes in node_list
#         get the ips from kubectl or /etc/hosts file
#         :param node_list: list of nodes names hostnames which pods lives on
#         """
#         self.set_nodes()
#         self.__write_to_host_file(node_list, user_input)
#
#     def __write_to_host_file(self, node_list, user_input):
#         """
#         :param nodes_list: list of nodes that pods lives on
#         :param user_input: user input
#         write to hosts and ip address of the nodes that pods lives on
#         """
#         pass
#
#     def prepare_ansible_env(self, node_list, user_input):
#         """
#         1- creates ansible config file in the running env
#         2- create inventory for the workers we need to run on in the curr running env
#         :param nodes_list: list of nodes that pods lives on
#         :param user_input: user input
#         :return:
#         """
#         self.__create_ansible_config()
#         self.__create_host_file(node_list, user_input)
#
#     def run_playbook(self, playbook_path, params=None):
#         """
#         function that runs playbook with params
#         :param playbook_path: the playbook name
#         :param params: ansible playbook params, dictionary key is param name and value is the value
#         """
#         params_str_ansible_format = ' '.join(['{}={}'.format(key, value) for key, value in params.items()])
#         command = 'sudo ansible-playbook -f 150 -i {} --extra-vars "{}" {}'.format(self.inventory_path,
#                                                                                    params_str_ansible_format,
#                                                                                    playbook_path)
#         shell_exec(command)
