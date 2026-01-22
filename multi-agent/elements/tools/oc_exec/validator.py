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
    """Validates OpenShift connection."""

    def validate(
        self,
        config: OcExecToolConfig,
        context: ValidationContext,
    ) -> ValidatorReport:
        messages: List[ValidationMessage] = []

        try:
            with oc.api_server(config.server):
                with oc.token(config.token):
                    with oc.tls_verify(enable=not config.insecure_skip_tls_verify):
                        result = oc.invoke('whoami')
            
            stdout = result.out().strip() if result.out() else ""
            stderr = result.err().strip() if result.err() else ""
            
            if result.status() == 0:
                messages.append(self._info(
                    "CONNECTION_OK",
                    f"Connected to {config.server} as {stdout}",
                    field="server",
                ))
            else:
                messages.append(self._error(
                    ValidationCode.NETWORK_ERROR.value,
                    stderr or stdout or "Connection failed",
                    field="server",
                ))

        except oc.OpenShiftPythonException as e:
            messages.append(self._error(
                ValidationCode.NETWORK_ERROR.value,
                str(e),
                field="server",
            ))
                
        except Exception as e:
            messages.append(self._error(
                ValidationCode.NETWORK_ERROR.value,
                str(e),
                field="server",
            ))

        return self._build_report(messages=messages)
