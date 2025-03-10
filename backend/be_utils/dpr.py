from enum import Enum
from be_utils.utils import shell_exec,helm_response


class DPRCommands(Enum):
    INSTALL     = "helm install -f {values}  {deployment_name} /opt/app-root/src/pipelines/pre_training_helm --output json"
    UNINSTALL   = "helm uninstall {deployment_name} "
    STATUS      = "helm status {deployment_name} "
    UPGRADE     = "helm upgrade {deployment_name} --reuse-values /opt/app-root/src/pipelines/pre_training_helm {helm_set_params} --output json"
    RMQROUTE    = "oc get svc {deployment_name}-rabbitmq-svc -o jsonpath={spec}"
    DBROUTE     = "oc get svc {deployment_name}-mongodb-svc -o jsonpath={spec}"


class DPR:
    def __init__(self, api_url, token, namespace=None):
        self.api_url = api_url
        self.token = token
        self.namespace = namespace


    def run_dpr_command(self, command: DPRCommands, **kwargs):

        if not isinstance(command, DPRCommands):
            return helm_response(False, f"Error: Invalid Helm command {command}")

        command_str = command.value.format(**kwargs).strip()
        rc, stdout = shell_exec(command_str)

        return helm_response(rc == 0, stdout.strip())