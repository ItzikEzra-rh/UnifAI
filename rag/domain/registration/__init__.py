"""Registration domain - models and port interface."""
from .model import BaseSourceData, DocumentSourceData, SlackSourceData
from .port import RegistrationPort

__all__ = [
    "BaseSourceData",
    "DocumentSourceData",
    "SlackSourceData",
    "RegistrationPort",
]
