from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    """
    Immutable, easy-to-test representation of one turn in a conversation.
    SRP: only holds `role` + `content`.
    """
    role: Role
    content: str
