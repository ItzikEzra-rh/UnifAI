from enum import StrEnum

STREAM_PREFIX = "mas:stream:"


class StreamField(StrEnum):
    PAYLOAD = "payload"
    CONTROL = "__control"


class ControlSignal(StrEnum):
    CLOSE = "close"
