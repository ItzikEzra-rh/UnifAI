import asyncio
import time
import logging
from typing import Optional

from .transport_manager import TransportManager


class HealthCheckError(Exception):
    """Raised when a health check operation itself fails."""
    pass


class HealthChecker:
    """
    Responsible *only* for:
      1) Deciding when the connection needs a fresh “ping”
      2) Running that ping via TransportManager._session.list_tools()
      3) Optionally forcing a reconnect if “ping” fails or is stale.

    Construction:
        health = HealthChecker(transport_manager, timeout=5.0, interval=30.0)

    Methods:
        - is_actually_connected(): returns True/False if recent “ping” succeeded
        - ensure_connected(force_check=False): if not connected or stale, re-establish
    """

    def __init__(
            self,
            transport: TransportManager,
            timeout: float = 5.0,
            interval: float = 30.0
    ):
        self.transport = transport
        self.health_check_timeout = timeout
        self.health_check_interval = interval
        self._last_health_check: Optional[float] = None

    async def is_actually_connected(self) -> bool:
        """
        Returns True if:
          - transport.is_connected is True
          - we have done a “ping” in the last `health_check_interval` seconds
            OR a new “ping” (list_tools()) succeeds within `health_check_timeout` seconds.
        Otherwise, mark disconnected and return False.
        """
        if not self.transport.is_connected:
            return False

        now = time.time()
        if self._last_health_check and (now - self._last_health_check < self.health_check_interval):
            return True

        # Perform a real “ping” via list_tools()
        session = self.transport._session  # type: ignore
        try:
            await asyncio.wait_for(session.list_tools(), timeout=self.health_check_timeout)
            self._last_health_check = now
            return True
        except asyncio.TimeoutError:
            print("Health check timed out (%gs)", self.health_check_timeout)
            return False
        except Exception as e:
            print("Health check failed: %s", e)
            return False

    async def ensure_connected(self, force_check: bool = False) -> None:
        """
        Guarantee that `transport` is connected and healthy. If not:
          - Call transport.connect()
          - OR if already connected but ping failed/stale, call transport.disconnect() then connect()
        """
        if not self.transport.is_connected:
            await self.transport.connect()
            self._last_health_check = time.time()
            return

        if force_check or not await self.is_actually_connected():
            print("HealthChecker: stale or forced check → reconnecting")
            await self.transport.disconnect()
            await self.transport.connect()
            self._last_health_check = time.time()
