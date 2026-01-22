from typing import Literal, Optional
from pydantic import Field
from elements.tools.common.base_config import BaseToolConfig
from core.field_hints import SecretHint
from .identifiers import Identifier


class OcExecToolConfig(BaseToolConfig):
    """
    Configuration for the OpenShift OC execution tool.
    Supports token-based authentication for cluster access.
    """
    type: Literal[Identifier.TYPE] = Identifier.TYPE
    server: str = Field(
        ..., 
        description="OpenShift API server URL (e.g., https://api.cluster.example.com:6443)"
    )
    token: str = Field(
        ..., 
        description="OpenShift authentication token (e.g., sha256~...)",
        json_schema_extra=SecretHint(
            reason="Token credential should be masked",
            allow_reveal=False
        ).to_hints()
    )
    namespace: Optional[str] = Field(
        None,
        description="Default namespace/project to use (optional, uses cluster default if not set)"
    )
    insecure_skip_tls_verify: bool = Field(
        False,
        description="Skip TLS certificate verification (not recommended for production)"
    )
