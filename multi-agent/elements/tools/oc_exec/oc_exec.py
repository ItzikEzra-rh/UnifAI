import openshift_client as oc
import shlex
from typing import Any, Optional
from pydantic import BaseModel, Field
from elements.tools.common.base_tool import BaseTool


class OcCommandInput(BaseModel):
    cmd: str = Field(
        ..., 
        description="The oc command to execute (without 'oc' prefix, e.g., 'get pods', 'describe deployment myapp')"
    )


class OcExecTool(BaseTool):
    """Execute OpenShift 'oc' commands on a cluster."""
    
    name: str = "OcExecTool"
    description: str = "Execute oc commands on an OpenShift cluster"
    args_schema = OcCommandInput

    def __init__(
        self,
        *,
        server: str,
        token: str,
        namespace: Optional[str] = None,
        insecure_skip_tls_verify: bool = False,
    ):
        super().__init__()
        self._server = server
        self._token = token
        self._namespace = namespace
        self._skip_tls = insecure_skip_tls_verify
        
        # Create unique tool name
        safe_server = server.replace("https://", "").replace("http://", "")
        for char in '.:- /':
            safe_server = safe_server.replace(char, '_')
        self.name = f"oc_exec_{safe_server}"
        
        # Set description
        ns_info = f" (namespace: {namespace})" if namespace else ""
        self.description = (
            f"Execute 'oc' commands on OpenShift cluster {server}{ns_info}. "
            f"Provide commands without the 'oc' prefix. "
            f"Examples: 'get pods', 'describe pod mypod', 'logs deployment/myapp'"
        )
        
        # Verify connection
        self._run_oc(['whoami'])

    def _run_oc(self, cmd_parts: list) -> str:
        """Run an oc command and return combined output."""
        if not cmd_parts:
            return "Error: Empty command"
        
        verb = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        with oc.api_server(self._server):
            with oc.token(self._token):
                with oc.tls_verify(enable=not self._skip_tls):
                    if self._namespace and '-n' not in cmd_parts and '--namespace' not in cmd_parts:
                        with oc.project(self._namespace):
                            result = oc.invoke(verb, args)
                    else:
                        result = oc.invoke(verb, args)
        
        stdout = result.out().strip() if result.out() else ""
        stderr = result.err().strip() if result.err() else ""
        
        # Return both stdout and stderr
        output_parts = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"stderr: {stderr}")
        
        return "\n".join(output_parts) if output_parts else "(no output)"

    def run(self, *args: Any, **kwargs: Any) -> str:
        inp = self.args_schema(**kwargs)
        cmd_parts = shlex.split(inp.cmd)
        
        try:
            return self._run_oc(cmd_parts)
        except oc.OpenShiftPythonException as e:
            return str(e)
        except Exception as e:
            return str(e)
