class OpenStackApi:
    def __init__(self):
        pass

    def stack_list(self, project_name=''):
        raise NotImplementedError

    def project_list(self):
        raise NotImplementedError

    def server_list(self, project='--all-projects'):
        raise NotImplementedError

    def stack_resource_list(self, stack_id):
        raise NotImplementedError

    def port_list(self, physical_resource_id):
        raise NotImplementedError

    def server_info(self, physical_resource_id):
        raise NotImplementedError

    def baremetal_server_list(self):
        raise NotImplementedError

    def baremetal_server_show(self, uid):
        raise NotImplementedError

    def network_list(self):
        raise NotImplementedError

    def security_group_list(self):
        raise NotImplementedError

    def security_group_show(self, uid):
        raise NotImplementedError
