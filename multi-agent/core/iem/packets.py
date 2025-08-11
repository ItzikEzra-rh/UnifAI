"""
IEM Packet Models

Defines the packet hierarchy for Inter-Element Messaging protocol.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import uuid
from .models import ElementAddress, IEMError, PacketKind


class BaseIEMPacket(BaseModel):
    """Base packet for all IEM communications."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol: str = "iem/1.0"
    kind: str  # Defined by subclasses
    thread_id: Optional[str] = None
    ts: datetime = Field(default_factory=datetime.utcnow)
    ttl: Optional[timedelta] = None
    src: ElementAddress
    dst: ElementAddress

    ack_by: set[str] = Field(default_factory=set)
    
    @property
    def is_expired(self) -> bool:
        """Check if packet has expired based on TTL."""
        return self.ttl is not None and (datetime.utcnow() - self.ts) > self.ttl
    
    def acknowledge(self, uid: str) -> None:
        """Mark packet as acknowledged by given uid."""
        self.ack_by.add(uid)
    
    def is_acknowledged_by(self, uid: str) -> bool:
        """Check if packet is acknowledged by given uid."""
        return uid in self.ack_by


class RequestPacket(BaseIEMPacket):
    """Request packet for action invocation."""
    kind: PacketKind = PacketKind.REQUEST
    action: str
    args: dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[timedelta] = None
    
    @field_validator('action')
    @classmethod
    def action_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Action cannot be empty")
        return v.strip()


class ResponsePacket(BaseIEMPacket):
    """Response packet for request completion."""
    kind: PacketKind = PacketKind.RESPONSE
    correlation_id: str
    result: Optional[dict[str, Any]] = None
    error: Optional[IEMError] = None
    
    @field_validator('correlation_id')
    @classmethod
    def correlation_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Correlation ID cannot be empty")
        return v.strip()
    
    @field_validator('error')
    @classmethod
    def result_xor_error(cls, v, info):
        """Ensure exactly one of result or error is provided."""
        values = info.data
        result = values.get('result')
        error = v
        if (result is None) == (error is None):
            raise ValueError("Exactly one of result or error must be provided")
        return v


class EventPacket(BaseIEMPacket):
    """Event packet for notifications."""
    kind: PacketKind = PacketKind.EVENT
    event_type: str
    data: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('event_type')
    @classmethod
    def event_type_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Event type cannot be empty")
        return v.strip()


# Union type for all packet types
IEMPacket = Union[RequestPacket, ResponsePacket, EventPacket]
