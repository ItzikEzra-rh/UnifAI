"""
IEM Capable Mixin for Message-Driven Nodes

Provides opt-in IEM protocol support with channel permissions,
message processing loop, and handler hooks.
"""

from typing import Optional, Any, TypeVar, Generic
from graph.state.state_view import StateView
from graph.state.graph_state import Channel
from core.iem.packets import RequestPacket, ResponsePacket, EventPacket
from core.iem.models import IEMError
from core.iem.interfaces import InterMessenger
from core.iem.factory import messenger_from_ctx
from core.contracts import SupportsStateContext

# -----------------------------------------------------------------------------
# Type variable bound to the minimal "SupportsStateContext" Protocol.
# TSupportsState represents any class that implements state/context interface:
#  - |get_state() -> StateView
#  - |get_context() -> StepContext
# This ensures static type checkers know `self` has state/context capability.
# -----------------------------------------------------------------------------
TSupportsState = TypeVar("TSupportsState", bound=SupportsStateContext)


class IEMCapableMixin(Generic[TSupportsState]):
    """
    Mixin for nodes that use the IEM protocol.
    
    Generic[TSupportsState]:
        - Declares that `self` must implement the SupportsStateContext protocol.
        - Enables static analyzers to recognize ._state and ._ctx.
    
    Responsibilities:
      1. Enforce at subclass-definition that the host class provides state/context.
      2. Initialize IEM-related attributes and lazy messenger.
      3. Provide message processing loop and handler hooks.
      4. Provide convenience methods delegating to messenger.

    Requirements on `self` (from SupportsStateContext Protocol):
      - `get_state() -> StateView`
      - `get_context() -> StepContext`
    """
    
    # Channel permissions (inherited by MRO)
    MIXIN_READS = {Channel.INTER_PACKETS}
    MIXIN_WRITES = {Channel.INTER_PACKETS}
    
    # No class-level filtering - let nodes handle their own filtering in handle_* methods

    def __init_subclass__(cls) -> None:
        """
        At subclass definition time, ensure the concrete class implements
        the state/context protocol and declares required channels.
        """
        if not issubclass(cls, SupportsStateContext):
            raise TypeError(
                f"{cls.__name__} requires state/context support (get_state() + get_context())."
            )
        
        super().__init_subclass__()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._iem_ms: Optional[InterMessenger] = None
    
    @property
    def ms(self: TSupportsState) -> InterMessenger:
        """Access to IEM messenger - lazily initialized."""
        if self._iem_ms is None:
            try:
                state = self.get_state()
                context = self.get_context()
            except RuntimeError:
                raise RuntimeError("IEM messenger not available outside of run()")
            self._iem_ms = messenger_from_ctx(state, context)
        return self._iem_ms

    @property  
    def messenger(self: TSupportsState) -> InterMessenger:
        """Access to IEM messenger - lazily initialized."""
        return self.ms
    
    def process_messages(self, state: StateView) -> None:
        """
        Process incoming IEM messages from inbox.
        
        Processes all requests, responses, and events, calling appropriate 
        handlers and acknowledging each message. Individual nodes should 
        implement filtering logic in their handle_* methods as needed.
        """
        # Process requests
        for req in self.inbox_requests():
            try:
                self.handle_request(req)
            finally:
                self.acknowledge(req.id)
        
        # Process responses
        for resp in self.inbox_responses():
            try:
                self.handle_response(resp)
            finally:
                self.acknowledge(resp.id)
        
        # Process events  
        for evt in self.inbox_events():
            try:
                self.handle_event(evt)
            finally:
                self.acknowledge(evt.id)
    
    def process_messages_for_thread(self, state: StateView, thread_id: str) -> None:
        """
        Process IEM messages for a specific thread only.
        
        Convenience method for nodes that want to process only messages
        from a specific workflow thread.
        """
        # Process requests for this thread
        for req in self.inbox_requests(thread_id=thread_id):
            try:
                self.handle_request(req)
            finally:
                self.acknowledge(req.id)
        
        # Process responses for this thread
        for resp in self.inbox_responses(thread_id=thread_id):
            try:
                self.handle_response(resp)
            finally:
                self.acknowledge(resp.id)
        
        # Process events for this thread
        for evt in self.inbox_events(thread_id=thread_id):
            try:
                self.handle_event(evt)
            finally:
                self.acknowledge(evt.id)
    
    def handle_request(self, request: RequestPacket) -> None:
        """
        Override to handle incoming request packets.
        
        Default implementation does nothing.
        """
        pass
    
    def handle_response(self, response: ResponsePacket) -> None:
        """
        Override to handle incoming response packets.
        
        Default implementation does nothing.
        """
        pass
    
    def handle_event(self, event: EventPacket) -> None:
        """
        Override to handle incoming event packets.
        
        Default implementation does nothing.  
        """
        pass
    
    # ===== Convenience delegates to messenger =====
    
    def inbox_requests(self, **kwargs) -> list[RequestPacket]:
        """Get incoming request packets. Delegates to messenger."""
        return self.ms.inbox_requests(**kwargs)
    
    def inbox_events(self, **kwargs) -> list[EventPacket]:
        """Get incoming event packets. Delegates to messenger."""
        return self.ms.inbox_events(**kwargs)
    
    def inbox_responses(self, **kwargs):
        """Get incoming response packets. Delegates to messenger."""
        return self.ms.inbox_responses(**kwargs)
    
    def send_request(self, *args, **kwargs) -> str:
        """Send request packet. Delegates to messenger."""
        return self.ms.send_request(*args, **kwargs)
    
    def send_event(self, *args, **kwargs) -> str:
        """Send event packet. Delegates to messenger."""
        return self.ms.send_event(*args, **kwargs)
    
    def reply(self, request: RequestPacket, *, result: dict = None, 
             error: IEMError = None) -> str:
        """Reply to request packet. Delegates to messenger."""
        return self.ms.reply(request, result=result, error=error)
    
    def for_thread(self, thread_id: str):
        """Get thread-scoped messenger view. Delegates to messenger."""
        return self.ms.for_thread(thread_id)
    
    def broadcast_event(self, event_type: str, data: dict = None, **kwargs) -> list[str]:
        """Broadcast event to all adjacent nodes. Delegates to messenger."""
        return self.ms.broadcast_event(event_type, data or {}, **kwargs)
    
    def acknowledge(self, packet_id: str) -> bool:
        """Acknowledge packet. Delegates to messenger."""
        return self.ms.acknowledge(packet_id)
    
    def purge(self, **kwargs) -> int:
        """Purge old packets from state. Delegates to messenger."""
        return self.ms.purge(**kwargs)