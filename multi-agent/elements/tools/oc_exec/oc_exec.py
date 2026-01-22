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
    """
    Execute OpenShift 'oc' commands using the openshift-client Python library.
    Provides a Pythonic interface to OpenShift cluster operations.
    """
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
        self._insecure_skip_tls_verify = insecure_skip_tls_verify
        
        # Create unique tool name from server
        translation = str.maketrans('.:- /', '_____')
        safe_server = server.replace("https://", "").replace("http://", "").translate(translation)
        self.name = f"oc_exec_{safe_server}"
        
        # Create descriptive description
        ns_info = f" in namespace '{namespace}'" if namespace else ""
        self.description = (
            f"Execute OpenShift 'oc' commands on cluster at {server}{ns_info}.\n\n"
            f"This tool automatically authenticates to the OpenShift cluster and executes "
            f"the command you provide. You only need to specify the oc command.\n\n"
            f"Connection Details:\n"
            f"• Server: {server}\n"
            + (f"• Default Namespace: {namespace}\n" if namespace else "")
            + f"\nUsage: Provide the oc command WITHOUT the 'oc' prefix.\n"
            f"Examples:\n"
            f"  • 'get pods' → lists all pods\n"
            f"  • 'get pods -n myproject' → lists pods in specific namespace\n"
            f"  • 'describe pod mypod' → describes a pod\n"
            f"  • 'logs deployment/myapp' → gets logs from deployment\n"
            f"  • 'get routes -o yaml' → gets routes in YAML format"
        )
        
        # Verify connection on init
        self._verify_connection()

    def _invoke_oc(self, cmd_parts: list):
        """
        Invoke oc command with proper argument format.
        oc.invoke expects: verb (str), args (list)
        e.g., oc.invoke('get', ['pods', '-n', 'default'])
        """
        if not cmd_parts:
            raise ValueError("Empty command")
        
        verb = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        return oc.invoke(verb, args)

    def _execute_with_context(self, func):
        """Execute a function within the proper oc context (api_server + token + tls)."""
        with oc.api_server(self._server):
            with oc.token(self._token):
                if self._insecure_skip_tls_verify:
                    with oc.tls_verify(enable=False):
                        if self._namespace:
                            with oc.project(self._namespace):
                                return func()
                        else:
                            return func()
                else:
                    if self._namespace:
                        with oc.project(self._namespace):
                            return func()
                    else:
                        return func()

    def _verify_connection(self) -> None:
        """Verify we can connect to the cluster."""
        try:
            def check_whoami():
                result = self._invoke_oc(['whoami'])
                if result.status() != 0:
                    raise RuntimeError(f"Authentication failed: {result.err()}")
                return result.out().strip()
            
            user = self._execute_with_context(check_whoami)
            # Connection successful
        except oc.OpenShiftPythonException as e:
            raise RuntimeError(f"Failed to connect to OpenShift cluster: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to OpenShift cluster: {e}")

    def run(self, *args: Any, **kwargs: Any) -> str:
        inp = self.args_schema(**kwargs)
        
        try:
            # Parse the command - split by spaces but respect quotes
            cmd_parts = shlex.split(inp.cmd)
            
            if not cmd_parts:
                return "ERROR: Empty command provided"
            
            def execute_command():
                # Check if command already has -n flag, if so don't use project context
                if '-n' in cmd_parts or '--namespace' in cmd_parts:
                    # Don't wrap in project context, command has its own namespace
                    with oc.api_server(self._server):
                        with oc.token(self._token):
                            if self._insecure_skip_tls_verify:
                                with oc.tls_verify(enable=False):
                                    return self._invoke_oc(cmd_parts)
                            else:
                                return self._invoke_oc(cmd_parts)
                else:
                    return self._invoke_oc(cmd_parts)
            
            result = self._execute_with_context(execute_command)
            
            if result.status() != 0:
                stderr = result.err().strip() if result.err() else ""
                stdout = result.out().strip() if result.out() else ""
                error_output = stderr or stdout or "Unknown error"
                return f"Error (exit code {result.status()}):\n{error_output}"
            
            output = result.out().strip() if result.out() else ""
            return output if output else "(no output)"
                
        except oc.OpenShiftPythonException as e:
            return f"ERROR: OpenShift command failed: {str(e)}"
        except Exception as e:
            return f"ERROR: Unexpected error: {str(e)}"
