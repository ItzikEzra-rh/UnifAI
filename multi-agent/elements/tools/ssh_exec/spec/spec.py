from elements.common.base_element_spec import BaseElementSpec
from core.enums import ResourceCategory
from ..config import SshExecToolConfig
from ..ssh_exec_factory import SshExecToolFactory
from ..identifiers import ELEMENT_TYPE_KEY


class SshExecToolElementSpec(BaseElementSpec):
    """Element specification for SSH Exec Tool."""

    category = ResourceCategory.TOOL
    type_key = ELEMENT_TYPE_KEY
    name = "SSH Exec"
    description = "Execute a shell command on a remote VM"
    config_schema = SshExecToolConfig
    factory_cls = SshExecToolFactory
    tags = ["tool", "ssh", "exec", "remote", "execution"]
