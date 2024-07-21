class KubernetesApi:
    def __init__(self):
        pass

    def pods_list(self, namespace=None):
        raise NotImplementedError

    def deployments_list(self):
        raise NotImplementedError

    def get_pod(self, pod_name, namespace, output_type='json'):
        raise NotImplementedError

    def host_list(self):
        raise NotImplementedError

    def get_deployment(self, deployment_name, namespace, output_type='json'):
        raise NotImplementedError

    def get_networks_attachments(self):
        raise NotImplementedError

    def get_k8s_version(self):
        raise NotImplementedError

    def get_vip_network(self, output_type='json'):
        raise NotImplementedError
