from typing import Optional
from mcp import ClientSession
from mcp.client.sse import sse_client


class McpConnectionError(Exception):
    """Raised when the SSE connection cannot be established or fails."""
    pass


class TransportManager:
    """
    Responsible *only* for:
      1) Opening an SSE transport (via mcp.client.sse.sse_client)
      2) Creating a ClientSession over that transport
      3) Disconnecting/cleaning up both the ClientSession and SSE generator

    Usage:
        transport = TransportManager("http://host:8004/sse", sampling_callback=my_cb)
        await transport.connect()
        # ... use transport._session to call tools ...
        await transport.disconnect()

        # or via `async with transport:`
    """

    def __init__(self, sse_endpoint: str, sampling_callback=None):
        self.sse_endpoint = sse_endpoint
        self.sampling_callback = sampling_callback

        # These get set on connect()
        self._transport_context = None  # will hold the SSE generator context
        self._read_stream = None  # async iterator from sse_client().__aenter__()
        self._write_stream = None  # writer coroutine from sse_client().__aenter__()
        self._session: Optional[ClientSession] = None

        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """
        Returns True if:
          - We opened the SSE transport successfully
          - We created a ClientSession over that transport
        """
        return self._is_connected and (self._session is not None)

    async def connect(self) -> None:
        """
        Open the SSE transport and start a ClientSession. Idempotent if already connected.
        Raises McpConnectionError if anything fails.
        """
        if self.is_connected:
            return

        # 1) If there's any half‐open state, clean it out first
        await self._safe_cleanup()

        # 2) Create SSE generator context
        try:
            print("Opening SSE transport to %s", self.sse_endpoint)
            self._transport_context = sse_client(url=self.sse_endpoint)
            self._read_stream, self._write_stream = await self._transport_context.__aenter__()
        except Exception as e:
            self._transport_context = None
            raise McpConnectionError(f"SSE transport failed: {e}")

        # 3) Create & initialize ClientSession over that transport
        try:
            self._session = ClientSession(
                self._read_stream,
                self._write_stream,
                sampling_callback=self.sampling_callback
            )
            await self._session.__aenter__()
            await self._session.initialize()
        except Exception as e:
            # If session init fails, ensure SSE context is torn down
            await self._transport_context.__aexit__(None, None, None)
            self._transport_context = None
            self._session = None
            raise McpConnectionError(f"ClientSession initialization failed: {e}")

        self._is_connected = True
        print("TransportManager: connected successfully")

    async def disconnect(self) -> None:
        """
        Cleanly close the ClientSession and then the SSE transport.
        If not connected, no‐op.
        """
        if not self.is_connected:
            return

        self._is_connected = False
        # 1) Close the ClientSession
        try:
            await self._session.__aexit__(None, None, None)
        except Exception as e:
            print("Error while closing ClientSession: %s", e)
        finally:
            self._session = None

        # 2) Close the SSE generator
        try:
            await self._transport_context.__aexit__(None, None, None)
        except Exception as e:
            # SSE generators often raise a GeneratorExit or RuntimeError—log at debug
            print("TransportManager: SSE cleanup got expected error: %s", e)
        finally:
            self._transport_context = None
            self._read_stream = None
            self._write_stream = None

        print("TransportManager: disconnected")

    async def _safe_cleanup(self) -> None:
        """
        If a previous session or transport is still open, tear it down quietly.
        Used at the start of connect() to avoid half‐open state.
        """
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
            self._session = None

        if self._transport_context:
            try:
                await self._transport_context.__aexit__(None, None, None)
            except Exception:
                pass
            self._transport_context = None
            self._read_stream = None
            self._write_stream = None

    # Allow `async with transport:` to connect/disconnect automatically
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()
