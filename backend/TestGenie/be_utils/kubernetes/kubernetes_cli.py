from .kubernetes_api import KubernetesApi
from be_utils.utils import shell_exec
from be_utils.kubernetes.kubernetes_utils import parse_k8s_version


class Cli(KubernetesApi):
    def __init__(self):
        super(Cli, self, ).__init__()

    def pods_list(self, namespace=None, output_type='json'):
        """
        Function that get pods
        if namespace is None, then get all namespaces pods
        if namespace is not Not, then get pods in that specific namespace
        :return:
        """
        namespace = f'-n {namespace}' if namespace else '-A'
        rc, stdout = shell_exec(f'kubectl get pods {namespace} -o {output_type}')
        return rc, stdout

    def deployments_list(self, namespace=None, output_type='json'):
        """
        Function that gets all deployments
        :return:
        """
        namespace = f'-n {namespace}' if namespace else '-A'
        rc, stdout = shell_exec(f'kubectl get deployments {namespace} -o {output_type}')
        return rc, stdout

    def get_pod(self, pod_name, namespace, output_type='json'):
        rc, stdout = shell_exec(f'kubectl get pod {pod_name} -n {namespace} -o {output_type}')
        return rc, stdout

    def host_list(self, output_type='json'):
        rc, stdout = shell_exec(f'kubectl get nodes -o {output_type}')
        return rc, stdout

    def get_deployment(self, deployment_name, namespace, output_type='json'):
        rc, stdout = shell_exec(f'kubectl get deployment {deployment_name} -n {namespace} -o {output_type}')
        return rc, stdout

    def get_networks_attachments(self, output_type='json'):
        rc, stdout = shell_exec(f'kubectl get network-attachment-definitions.k8s.cni.cncf.io -A -o {output_type}')
        return rc, stdout

    def get_calico_network(self, output_type='json'):
        rc, stdout = shell_exec(f'/usr/local/sbin/calicoctl get ipPool -o {output_type}')
        return rc, stdout

    def get_k8s_version(self):
        rc, stdout = shell_exec('kubectl version --short')
        version = parse_k8s_version(stdout)
        return version

    def get_vip_network(self, output_type='json'):
        rc, stdout = shell_exec(f'kubectl get virtualipinstancegroup -A -o {output_type}')
        return rc, stdout
