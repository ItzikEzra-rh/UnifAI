"""
Redis-backed channel factory.

Creates session-scoped writers (RedisSessionChannel) and readers
(RedisSessionChannelReader) backed by Redis Streams. A single
connection pool is shared across all channels.
"""
from redis import ConnectionPool, Redis

from mas.core.channels import ChannelFactory, SessionChannel, SessionChannelReader
from .channel import RedisSessionChannel
from .reader import RedisSessionChannelReader


class RedisChannelFactory(ChannelFactory):

    def __init__(
        self,
        redis_url: str,
        stream_ttl: int = 3600,
        block_ms: int = 5000,
        batch_size: int = 50,
    ) -> None:
        self._pool = ConnectionPool.from_url(redis_url)
        self._stream_ttl = stream_ttl
        self._block_ms = block_ms
        self._batch_size = batch_size

    def create(self, session_id: str) -> SessionChannel:
        return RedisSessionChannel(
            session_id,
            Redis(connection_pool=self._pool),
            ttl=self._stream_ttl,
        )

    def create_reader(self, session_id: str) -> SessionChannelReader:
        return RedisSessionChannelReader(
            session_id,
            Redis(connection_pool=self._pool),
            block_ms=self._block_ms,
            batch_size=self._batch_size,
        )
