"""
Redis Streams session channel — write side.

Each emit() appends an event to a Redis Stream keyed by session ID.
Streams persist events so that late-joining readers get full replay.

Control signals (close) use a separate field so that user data in
the payload field is never polluted.

TTL is configurable; set to 0 to persist streams forever.
"""
import json
from typing import Any

from redis import Redis

from mas.core.channels import SessionChannel
from .constants import STREAM_PREFIX, StreamField, ControlSignal


class RedisSessionChannel(SessionChannel):

    def __init__(self, session_id: str, redis_client: Redis, ttl: int = 3600) -> None:
        self._session_id = session_id
        self._redis = redis_client
        self._stream_key = f"{STREAM_PREFIX}{session_id}"
        self._ttl = ttl
        self._closed = False

    @property
    def session_id(self) -> str:
        return self._session_id

    def emit(self, data: Any) -> None:
        if self._closed:
            return
        self._redis.xadd(
            self._stream_key,
            {StreamField.PAYLOAD: json.dumps(data, default=str)},
        )
        self._touch_ttl()

    def is_active(self) -> bool:
        return not self._closed

    def close(self) -> None:
        self._redis.xadd(
            self._stream_key,
            {StreamField.CONTROL: ControlSignal.CLOSE},
        )
        self._touch_ttl()
        self._closed = True

    def supports_input(self) -> bool:
        return True

    def _touch_ttl(self) -> None:
        if self._ttl > 0:
            self._redis.expire(self._stream_key, self._ttl)
