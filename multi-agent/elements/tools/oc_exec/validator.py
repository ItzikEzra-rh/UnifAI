"""Validator for OpenShift OC Exec Tool."""
import openshift_client as oc
from typing import List

from elements.common.validator import (
    BaseElementValidator,
    ValidatorReport,
    ValidationContext,
    ValidationMessage,
    ValidationCode,
)
from elements.tools.oc_exec.config import OcExecToolConfig


class OcExecToolValidator(BaseElementValidator):
    """Validates OpenShift connection using openshift-client library."""

    def _invoke_oc(self, cmd_parts: list):
        """
        Invoke oc command with proper argument format.
        oc.invoke expects: verb (str), args (list)
        """
        if not cmd_parts:
            raise ValueError("Empty command")
        
        verb = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        return oc.invoke(verb, args)

    def validate(
        self,
        config: OcExecToolConfig,
        context: ValidationContext,
    ) -> ValidatorReport:
        messages: List[ValidationMessage] = []

        try:
            # Use nested context managers as per openshift-client-python docs
            with oc.api_server(config.server):
                with oc.token(config.token):
                    if config.insecure_skip_tls_verify:
                        with oc.tls_verify(enable=False):
                            result = self._invoke_oc(['whoami'])
                    else:
                        result = self._invoke_oc(['whoami'])
                    
                    if result.status() == 0:
                        user = result.out().strip() if result.out() else "unknown"
                        messages.append(self._info(
                            "CONNECTION_OK",
                            f"Successfully connected to OpenShift cluster at {config.server}",
                            field="server",
                        ))
                        messages.append(self._info(
                            "AUTH_OK",
                            f"Authenticated as: {user}",
                            field="token",
                        ))
                        
                        # Check namespace if specified
                        if config.namespace:
                            try:
                                with oc.project(config.namespace):
                                    ns_result = self._invoke_oc(['get', 'project', config.namespace])
                                    if ns_result.status() != 0:
                                        messages.append(self._warning(
                                            "NAMESPACE_WARNING",
                                            f"Namespace '{config.namespace}' may not exist or is not accessible",
                                            field="namespace",
                                        ))
                            except Exception:
                                messages.append(self._warning(
                                    "NAMESPACE_WARNING",
                                    f"Could not verify namespace '{config.namespace}'",
                                    field="namespace",
                                ))
                    else:
                        error_msg = result.err().strip() if result.err() else "Unknown error"
                        error_msg_lower = error_msg.lower()
                        
                        if "x509" in error_msg_lower or "certificate" in error_msg_lower:
                            messages.append(self._error(
                                ValidationCode.NETWORK_ERROR.value,
                                f"TLS/Certificate error. Consider enabling 'insecure_skip_tls_verify'.",
                                field="server",
                            ))
                        elif "unauthorized" in error_msg_lower or "token" in error_msg_lower or "forbidden" in error_msg_lower:
                            messages.append(self._error(
                                ValidationCode.INVALID_CREDENTIALS.value,
                                f"Authentication failed: Invalid or expired token",
                                field="token",
                            ))
                        elif "no such host" in error_msg_lower or "could not resolve" in error_msg_lower:
                            messages.append(self._error(
                                ValidationCode.ENDPOINT_UNREACHABLE.value,
                                f"Cannot resolve server hostname: {error_msg}",
                                field="server",
                            ))
                        elif "connection refused" in error_msg_lower:
                            messages.append(self._error(
                                ValidationCode.ENDPOINT_UNREACHABLE.value,
                                f"Connection refused: {error_msg}",
                                field="server",
                            ))
                        else:
                            messages.append(self._error(
                                ValidationCode.NETWORK_ERROR.value,
                                f"Connection failed: {error_msg}",
                                field="server",
                            ))

        except oc.OpenShiftPythonException as e:
            error_str = str(e).lower()
            if "x509" in error_str or "certificate" in error_str:
                messages.append(self._error(
                    ValidationCode.NETWORK_ERROR.value,
                    f"TLS/Certificate error: {e}. Consider enabling 'insecure_skip_tls_verify'.",
                    field="server",
                ))
            elif "unauthorized" in error_str or "forbidden" in error_str:
                messages.append(self._error(
                    ValidationCode.INVALID_CREDENTIALS.value,
                    f"Authentication failed: {e}",
                    field="token",
                ))
            else:
                messages.append(self._error(
                    ValidationCode.NETWORK_ERROR.value,
                    f"OpenShift error: {str(e)}",
                    field="server",
                ))
        except Exception as e:
            messages.append(self._error(
                ValidationCode.NETWORK_ERROR.value,
                f"Unexpected error: {type(e).__name__}: {str(e)}",
                field="server",
            ))

        return self._build_report(messages=messages)
