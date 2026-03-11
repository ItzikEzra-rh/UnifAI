from enum import Enum, auto


class SessionStatus(Enum):
    PENDING = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
