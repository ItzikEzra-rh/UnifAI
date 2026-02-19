from typing import List

import httpx

from elements.common.validator import (
    BaseElementValidator,
    ValidationCode,
    ValidationContext,
    ValidationMessage,
    ValidatorReport,
)
from .config import WebFetchToolConfig


class WebFetchToolValidator(BaseElementValidator):

    _PROBE_URL = "https://httpbin.org/status/200"

    def validate(
        self,
        config: WebFetchToolConfig,
        context: ValidationContext,
    ) -> ValidatorReport:
        messages: List[ValidationMessage] = []

        try:
            with httpx.Client(timeout=context.timeout_seconds) as client:
                response = client.head(self._PROBE_URL)

            if response.status_code == 200:
                messages.append(self._info("OUTBOUND_HTTP_OK", "Outbound HTTP connectivity verified"))
            else:
                messages.append(self._warning(
                    ValidationCode.NETWORK_ERROR.value,
                    f"HTTP probe returned status {response.status_code}",
                ))
        except httpx.TimeoutException:
            messages.append(self._error(
                ValidationCode.NETWORK_TIMEOUT.value,
                f"HTTP probe timed out after {context.timeout_seconds}s",
            ))
        except Exception as exc:
            messages.append(self._error(
                ValidationCode.NETWORK_ERROR.value,
                f"HTTP connectivity check failed: {type(exc).__name__}: {exc}",
            ))

        return self._build_report(messages=messages)
