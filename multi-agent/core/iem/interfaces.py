"""
IEM Protocol Interfaces

Defines the core interfaces for Inter-Element Messaging.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Union
from datetime import timedelta
from .packets import IEMPacket, RequestPacket, ResponsePacket, EventPacket
from .models import IEMError, PacketKind


class InterMessenger(ABC):
    """
    Core interface for inter-element messaging.
    
    Provides structured communication between graph elements via
    request/response and event patterns with correlation tracking.
    """
    
    @abstractmethod
    def send_request(self, to_uid: str, action: str, args: dict[str, Any] = None, 
                    *, timeout: timedelta = None, thread_id: str = None) -> str:
        """
        Send a request packet to another element.
        
        Args:
            to_uid: Target element UID
            action: Action to invoke
            args: Action arguments
            timeout: Request timeout
            thread_id: Optional thread grouping
            
        Returns:
            Packet ID for correlation
            
        Raises:
            IEMAdjacencyException: If to_uid is not adjacent (when enforced)
            IEMValidationException: If packet validation fails
        """
        pass
    
    @abstractmethod
    def send_response(self, request: RequestPacket, result: dict = None, 
                     error: IEMError = None) -> str:
        """
        Send a response to a request packet.
        
        Args:
            request: Original request packet
            result: Success result (mutually exclusive with error)
            error: Error result (mutually exclusive with result)
            
        Returns:
            Response packet ID
            
        Raises:
            IEMValidationException: If both or neither result/error provided
        """
        pass
    
    @abstractmethod
    def send_event(self, to_uid: str, event_type: str, data: dict[str, Any] = None,
                  *, thread_id: str = None) -> str:
        """
        Send an event packet to another element.
        
        Args:
            to_uid: Target element UID
            event_type: Type of event
            data: Event data
            thread_id: Optional thread grouping
            
        Returns:
            Event packet ID
            
        Raises:
            IEMAdjacencyException: If to_uid is not adjacent (when enforced)
        """
        pass
    
    @abstractmethod
    def inbox(self, kinds: set[PacketKind] = None) -> list[IEMPacket]:
        """
        Get unacknowledged packets addressed to this element.
        
        Args:
            kinds: Packet kinds to filter (default: {PacketKind.REQUEST, PacketKind.EVENT})
            
        Returns:
            List of unacknowledged packets
        """
        pass
    
    @abstractmethod
    def acknowledge(self, packet_id: str) -> bool:
        """
        Mark a packet as acknowledged.
        
        Args:
            packet_id: ID of packet to acknowledge
            
        Returns:
            True if packet was found and acknowledged
        """
        pass
    
    # ===== Enhanced API Methods =====
    
    @abstractmethod
    def inbox_requests(self, *, thread_id: str = None, from_uid: str = None, 
                      action: str = None) -> list[RequestPacket]:
        """
        Get incoming request packets with optional filtering.
        
        Args:
            thread_id: Filter by thread ID
            from_uid: Filter by sender UID
            action: Filter by action name
            
        Returns:
            List of matching unacknowledged request packets
        """
        pass
    
    @abstractmethod
    def inbox_events(self, *, thread_id: str = None, from_uid: str = None,
                    event_type: str = None) -> list[EventPacket]:
        """
        Get incoming event packets with optional filtering.
        
        Args:
            thread_id: Filter by thread ID
            from_uid: Filter by sender UID
            event_type: Filter by event type
            
        Returns:
            List of matching unacknowledged event packets
        """
        pass
    
    @abstractmethod
    def inbox_responses(self, *, thread_id: str = None, correlation_id: str = None,
                       from_uid: str = None) -> list[ResponsePacket]:
        """
        Get incoming response packets with optional filtering.
        
        Args:
            thread_id: Filter by thread ID
            correlation_id: Filter by correlation ID (original request ID)
            from_uid: Filter by sender UID
            
        Returns:
            List of matching unacknowledged response packets
        """
        pass
    
    @abstractmethod
    def reply(self, request: RequestPacket, *, result: dict = None, 
             error: IEMError = None) -> str:
        """
        Convenience method to reply to a request.
        
        Args:
            request: Original request packet to reply to
            result: Success result (mutually exclusive with error)
            error: Error result (mutually exclusive with result)
            
        Returns:
            Response packet ID
            
        Raises:
            IEMValidationException: If both or neither result/error provided
        """
        pass
    
    @abstractmethod
    def broadcast_event(self, event_type: str, data: dict[str, Any] = None,
                       *, thread_id: str = None) -> list[str]:
        """
        Send an event to all adjacent nodes.
        
        Args:
            event_type: Type of event
            data: Event data
            thread_id: Optional thread grouping
            
        Returns:
            List of packet IDs sent
        """
        pass
    
    @abstractmethod
    def for_thread(self, thread_id: str) -> 'InterMessenger':
        """
        Get a thread-scoped view of this messenger.
        
        All send methods will automatically include the thread_id,
        and inbox methods will automatically filter by thread_id.
        
        Args:
            thread_id: Thread to scope to
            
        Returns:
            Thread-scoped messenger view
        """
        pass
    
    @abstractmethod
    def purge(self, *, max_age: timedelta = None, acked_only: bool = True) -> int:
        """
        Remove old/acknowledged packets from the state.
        
        Args:
            max_age: Remove packets older than this (None = use messenger default)
            acked_only: Only remove acknowledged packets
            
        Returns:
            Number of packets removed
        """
        pass


class MessengerMiddleware(ABC):
    """
    Middleware interface for intercepting and modifying IEM packets.
    
    Allows for cross-cutting concerns like validation, logging,
    security checks, etc.
    """
    
    @abstractmethod
    def before_send(self, packet: IEMPacket) -> IEMPacket:
        """
        Called before sending a packet.
        
        Args:
            packet: Packet about to be sent
            
        Returns:
            Modified packet (or same packet)
            
        Raises:
            IEMException: To prevent sending
        """
        pass
    
    @abstractmethod
    def after_receive(self, packet: IEMPacket) -> IEMPacket:
        """
        Called after receiving a packet.
        
        Args:
            packet: Packet that was received
            
        Returns:
            Modified packet (or same packet)
            
        Raises:
            IEMException: To reject packet
        """
        pass
