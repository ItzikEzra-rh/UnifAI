"""
Default IEM Messenger Implementation

Production-ready implementation of the InterMessenger interface.
"""

from typing import Callable, Optional, Any
from datetime import timedelta, datetime
from graph.state.state_view import StateView
from graph.state.graph_state import Channel
from graph.step_context import StepContext
from .interfaces import InterMessenger, MessengerMiddleware
from .packets import RequestPacket, ResponsePacket, EventPacket, IEMPacket
from .models import ElementAddress, IEMError, PacketKind
from .exceptions import IEMException, IEMAdjacencyException, IEMValidationException


class DefaultInterMessenger(InterMessenger):
    """
    Default implementation of InterMessenger.
    
    Features:
    - Optional adjacency enforcement
    - Middleware support for cross-cutting concerns
    - Automatic packet filtering and TTL handling
    - Type-safe packet creation and validation
    """
    
    def __init__(
        self,
        state: StateView,
        identity: ElementAddress,
        *,
        is_adjacent: Optional[Callable[[str], bool]] = None,
        middleware: list[MessengerMiddleware] = None,
        max_packet_age: timedelta = timedelta(hours=24),
        context: Optional[StepContext] = None
    ):
        """
        Initialize messenger.
        
        Args:
            state: StateView for reading/writing channels
            identity: Address of this element
            is_adjacent: Function to check if UID is adjacent (None = no enforcement)
            middleware: List of middleware to apply
            max_packet_age: Maximum age for packets before they're considered expired
            context: StepContext for adjacency info (used for broadcast)
        """
        self._state = state
        self._me = identity
        self._is_adjacent = is_adjacent
        self._middleware = middleware or []
        self._max_packet_age = max_packet_age
        self._ctx = context
    
    def _apply_middleware_send(self, packet: IEMPacket) -> IEMPacket:
        """Apply before_send middleware in order."""
        for mw in self._middleware:
            packet = mw.before_send(packet)
        return packet
    
    def _apply_middleware_receive(self, packet: IEMPacket) -> IEMPacket:
        """Apply after_receive middleware in order."""
        for mw in self._middleware:
            packet = mw.after_receive(packet)
        return packet
    
    def _validate_send(self, to_uid: str) -> None:
        """Validate that send is allowed to target UID."""
        if self._is_adjacent and not self._is_adjacent(to_uid):
            raise IEMAdjacencyException(f"Non-adjacent send denied: {to_uid}")
    
    def _append_packet(self, packet: IEMPacket) -> None:
        """Apply middleware and append packet to state."""
        try:
            packet = self._apply_middleware_send(packet)
            # Get current packets and append new one
            current_packets = list(self._state.get(Channel.INTER_PACKETS, []))
            current_packets.append(packet)
            self._state[Channel.INTER_PACKETS] = current_packets
        except Exception as e:
            if isinstance(e, IEMException):
                raise
            raise IEMValidationException(f"Failed to send packet: {e}") from e
    
    def send_request(self, to_uid: str, action: str, args: dict[str, Any] = None,
                    *, timeout: timedelta = None, thread_id: str = None) -> str:
        """Send a request packet."""
        self._validate_send(to_uid)
        
        packet = RequestPacket(
            action=action,
            args=args or {},
            timeout=timeout,
            src=self._me,
            dst=ElementAddress(uid=to_uid),
            thread_id=thread_id
        )
        
        self._append_packet(packet)
        return packet.id
    
    def send_response(self, request: RequestPacket, result: dict = None,
                    error: IEMError = None) -> str:
        """Send a response packet."""
        if (result is None) == (error is None):
            raise IEMValidationException("Exactly one of result or error must be provided")
        
        packet = ResponsePacket(
            correlation_id=request.id,
            result=result,
            error=error,
            thread_id=request.thread_id,
            src=self._me,
            dst=request.src
        )
        
        self._append_packet(packet)
        return packet.id
    
    def send_event(self, to_uid: str, event_type: str, data: dict[str, Any] = None,
                  *, thread_id: str = None) -> str:
        """Send an event packet."""
        self._validate_send(to_uid)
        
        packet = EventPacket(
            event_type=event_type,
            data=data or {},
            src=self._me,
            dst=ElementAddress(uid=to_uid),
            thread_id=thread_id
        )
        
        self._append_packet(packet)
        return packet.id
    
    def inbox(self, kinds: set[PacketKind] = None) -> list[IEMPacket]:
        """Get unacknowledged packets addressed to this element."""
        kinds = kinds or {PacketKind.REQUEST, PacketKind.EVENT}
        packets = self._state.get(Channel.INTER_PACKETS, [])
        
        # Filter: addressed to me, right kind, not acked, not expired
        filtered = []
        for p in packets:
            if (p.dst.uid == self._me.uid and 
                p.kind in kinds and 
                not p.is_acknowledged_by(self._me.uid) and 
                not p.is_expired):
                try:
                    filtered_packet = self._apply_middleware_receive(p)
                    filtered.append(filtered_packet)
                except IEMException:
                    # Middleware rejected packet, skip it
                    continue
        
        return filtered
    
    def acknowledge(self, packet_id: str) -> bool:
        """Mark a packet as acknowledged."""
        packets = list(self._state.get(Channel.INTER_PACKETS, []))
        for p in packets:
            if p.id == packet_id:
                p.acknowledge(self._me.uid)
                self._state[Channel.INTER_PACKETS] = packets
                return True
        return False
    
    # ===== Enhanced API Implementation =====
    
    def inbox_requests(self, *, thread_id: str = None, from_uid: str = None, 
                      action: str = None) -> list[RequestPacket]:
        """Get incoming request packets with optional filtering."""
        packets = self.inbox(kinds={PacketKind.REQUEST})
        return self._filter_packets(packets, thread_id, from_uid, action=action)
    
    def inbox_events(self, *, thread_id: str = None, from_uid: str = None,
                    event_type: str = None) -> list[EventPacket]:
        """Get incoming event packets with optional filtering."""
        packets = self.inbox(kinds={PacketKind.EVENT})
        return self._filter_packets(packets, thread_id, from_uid, event_type=event_type)
    
    def inbox_responses(self, *, thread_id: str = None, correlation_id: str = None,
                       from_uid: str = None) -> list[ResponsePacket]:
        """Get incoming response packets with optional filtering."""
        packets = self.inbox(kinds={PacketKind.RESPONSE})
        return self._filter_packets(packets, thread_id, from_uid, correlation_id=correlation_id)
    
    def reply(self, request: RequestPacket, *, result: dict = None, 
             error: IEMError = None) -> str:
        """Convenience method to reply to a request."""
        return self.send_response(request, result=result, error=error)
    
    def broadcast_event(self, event_type: str, data: dict[str, Any] = None,
                       *, thread_id: str = None) -> list[str]:
        """Send an event to all adjacent nodes."""
        packet_ids = []
        
        # Use step context to get adjacent nodes
        if not self._ctx or not self._ctx.adjacent_nodes:
            return packet_ids
            
        for node_uid in self._ctx.adjacent_nodes.keys():
            try:
                packet_id = self.send_event(
                    to_uid=node_uid,
                    event_type=event_type,
                    data=data or {},
                    thread_id=thread_id
                )
                packet_ids.append(packet_id)
            except Exception:
                # Continue broadcasting to other nodes even if one fails
                continue
                
        return packet_ids
    
    def for_thread(self, thread_id: str) -> 'InterMessenger':
        """Get a thread-scoped view of this messenger."""
        return ThreadScopedMessenger(self, thread_id)
    
    def purge(self, *, max_age: timedelta = None, acked_only: bool = True) -> int:
        """Remove old/acknowledged packets from the state."""
        packets = list(self._state.get(Channel.INTER_PACKETS, []))
        initial_count = len(packets)
        
        now = datetime.utcnow()
        max_age = max_age or self._max_packet_age
        
        filtered = []
        for p in packets:
            # Check if should be purged
            should_purge = False
            
            if acked_only and p.is_acknowledged_by(self._me.uid):
                should_purge = True
            elif not acked_only and (p.is_expired or 
                                   (max_age and (now - p.ts) > max_age)):
                should_purge = True
            
            if not should_purge:
                filtered.append(p)
        
        if len(filtered) != initial_count:
            self._state[Channel.INTER_PACKETS] = filtered
            
        return initial_count - len(filtered)
    
    def _filter_packets(self, packets: list, thread_id: str = None, 
                       from_uid: str = None, **kwargs) -> list:
        """Helper to filter packets by common criteria."""
        filtered = []
        
        for packet in packets:
            # Thread filter
            if thread_id and getattr(packet, 'thread_id', None) != thread_id:
                continue
                
            # From UID filter
            if from_uid and packet.src.uid != from_uid:
                continue
            
            filtered.append(packet)
            
        return filtered


class ThreadScopedMessenger:
    """
    Thread-scoped view of an InterMessenger.
    
    Automatically includes thread_id in sends and filters by thread_id in inbox calls.
    """
    
    def __init__(self, messenger: InterMessenger, thread_id: str):
        self._messenger = messenger
        self._thread_id = thread_id
    
    def send_request(self, to_uid: str, action: str, args: dict[str, Any] = None, 
                    *, timeout: timedelta = None) -> str:
        """Send request with auto thread_id."""
        return self._messenger.send_request(
            to_uid, action, args, timeout=timeout, thread_id=self._thread_id
        )
    
    def send_event(self, to_uid: str, event_type: str, data: dict[str, Any] = None) -> str:
        """Send event with auto thread_id."""
        return self._messenger.send_event(to_uid, event_type, data, thread_id=self._thread_id)
    
    def broadcast_event(self, event_type: str, data: dict[str, Any] = None) -> list[str]:
        """Broadcast event with auto thread_id."""
        return self._messenger.broadcast_event(event_type, data, thread_id=self._thread_id)
    
    def inbox_requests(self, *, from_uid: str = None, action: str = None) -> list[RequestPacket]:
        """Get requests for this thread only."""
        return self._messenger.inbox_requests(
            thread_id=self._thread_id, from_uid=from_uid, action=action
        )
    
    def inbox_events(self, *, from_uid: str = None, event_type: str = None) -> list[EventPacket]:
        """Get events for this thread only."""
        return self._messenger.inbox_events(
            thread_id=self._thread_id, from_uid=from_uid, event_type=event_type
        )
    
    def inbox_responses(self, *, correlation_id: str = None, from_uid: str = None) -> list[ResponsePacket]:
        """Get responses for this thread only."""
        return self._messenger.inbox_responses(
            thread_id=self._thread_id, correlation_id=correlation_id, from_uid=from_uid
        )
    
    def reply(self, request: RequestPacket, *, result: dict = None, error: IEMError = None) -> str:
        """Reply to request (thread_id preserved automatically)."""
        return self._messenger.reply(request, result=result, error=error)
    
    def acknowledge(self, packet_id: str) -> bool:
        """Acknowledge packet."""
        return self._messenger.acknowledge(packet_id)

