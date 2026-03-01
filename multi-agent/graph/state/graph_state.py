from typing import Any, Callable, Dict, Iterator, List, Tuple, Set, get_type_hints
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ConfigDict
from elements.llms.common.chat.message import ChatMessage
from .merge_strategies import merge_string_dicts, append_chat_messages, merge_dynamic_fields, append_iem_packets, merge_task_threads, merge_threads, merge_workspaces
from enum import Enum


class GraphState(BaseModel):
    """
    Pydantic-backed execution state for LangGraph.

    • Declares your main channels with merge-strategies via Annotated
    • Allows arbitrary extra keys at runtime (extra="allow")
    • Behaves like a dict: __getitem__, __setitem__, keys(), items(), etc.
    • Properly handles state persistence across LangGraph nodes
    • Raises KeyError for non-existent keys (like standard dict)
    """
    model_config = ConfigDict(
        extra="allow",  # permit new keys on the fly
        arbitrary_types_allowed=True  # in case you store non‐JSON types
    )

    # —————– Channels (with merge strategies) —————–
    # last-writer-wins for user_prompt:
    user_prompt: Annotated[str, lambda old, new: new] = Field(
        default="", 
        json_schema_extra={'external': True, 'streamable': True}
    )
    # merge dicts into a new dict:
    nodes_output: Annotated[Dict[str, str], merge_string_dicts] = Field(
        default_factory=dict,
        json_schema_extra={'streamable': False}
    )

    # appending messages to a list:
    messages: Annotated[list[ChatMessage], append_chat_messages] = Field(
        default_factory=list,
        json_schema_extra={'streamable': True}
    )

    # last-writer-wins for output
    output: Annotated[str, lambda old, new: new] = Field(
        default="",
        json_schema_extra={'streamable': True}
    )

    target_branch: Annotated[str, lambda old, new: new] = Field(
        default="",
        json_schema_extra={'streamable': False}
    )

    # Dynamic storage for extra fields (will be included in serialization)
    dynamic_fields: Annotated[Dict[str, Any], merge_dynamic_fields] = Field(default_factory=dict)

    # —————– STRUCTURED COMMUNICATION (Inter-Node Coordination) —————–
    # IEM protocol packets for structured node-to-node communication
    inter_packets: Annotated[List[Any], append_iem_packets] = Field(
        default_factory=list,
        json_schema_extra={'streamable': False}  # Too large for streaming
    )
    
    # —————– PRIVATE WORKSPACE (Node Internal State) —————–

    # Task-focused conversation threads (agentic context)
    # Structure: {thread_id: [ChatMessage, ...]}
    task_threads: Annotated[Dict[str, List[ChatMessage]], merge_task_threads] = Field(
        default_factory=dict,
        json_schema_extra={'streamable': False}  # Too large for streaming
    )
    
    # —————– ENGENTIC WORKLOAD MANAGEMENT —————–
    # Thread metadata management (Thread objects)
    # Structure: {thread_id: Thread}
    threads: Annotated[Dict[str, Any], merge_threads] = Field(
        default_factory=dict,
        json_schema_extra={'streamable': False}  # Too large for streaming
    )
    
    # Workspace shared context management (Workspace objects)  
    # Structure: {thread_id: Workspace}
    workspaces: Annotated[Dict[str, Any], merge_workspaces] = Field(
        default_factory=dict,
        json_schema_extra={'streamable': False}  # Too large for streaming
    )

    # —————– Dict-like API —————–
    def __getitem__(self, key: str) -> Any:
        # 1) declared field?
        if key in self.__class__.model_fields:
            return getattr(self, key)
        # 2) dynamic field?
        if key in self.dynamic_fields:
            return self.dynamic_fields[key]
        # 3) not found anywhere - raise KeyError
        raise KeyError(f"{key!r} not found in state.")

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.__class__.model_fields:
            setattr(self, key, value)
        else:
            # Store in dynamic_fields which is preserved during serialization
            self.dynamic_fields[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self.__class__.model_fields:
            delattr(self, key)
        elif key in self.dynamic_fields:
            del self.dynamic_fields[key]
        else:
            raise KeyError(f"{key!r} not found in state.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Safe dictionary-like get method that doesn't raise KeyError
        """
        if key in self.__class__.model_fields:
            return getattr(self, key)
        return self.dynamic_fields.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self[k] = v

    def keys(self) -> Iterator[str]:
        return iter(list(self.__class__.model_fields.keys()) + list(self.dynamic_fields.keys()))

    @classmethod
    def get_external_channels(cls) -> Set[str]:
        """
        Returns names of all fields marked as external variables/channels
        """
        return set([field_name for field_name, field_info in cls.model_fields.items()
                    if field_info.json_schema_extra and field_info.json_schema_extra.get('external', False)])

    def items(self) -> Iterator[Tuple[str, Any]]:
        for k in self.__class__.model_fields:
            yield k, getattr(self, k)
        for k, v in self.dynamic_fields.items():
            yield k, v

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Override Pydantic's model_dump() to include both
        declared fields and dynamic extras.
        """
        base = super().model_dump(*args, **kwargs)
        # Remove dynamic_fields from base if present to avoid duplication
        if "dynamic_fields" in base:
            base.pop("dynamic_fields")
        return {**base, **self.dynamic_fields}

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Override Pydantic's model_dump() for compatibility
        """
        return self.dict(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dict()})"

    @classmethod
    def get_streamable_channels(cls) -> Set[str]:
        """
        Returns names of all fields marked as streamable.
        Only these fields will be included in stream payloads.
        
        Returns:
            Set of field names that have streamable=True in json_schema_extra
        """
        streamable = set()
        for field_name, field_info in cls.model_fields.items():
            if field_info.json_schema_extra:
                is_streamable = field_info.json_schema_extra.get('streamable', False)
                if is_streamable:
                    streamable.add(field_name)
        return streamable

    def get_streamable_state(self) -> Dict[str, Any]:
        """
        Returns a filtered dict containing only streamable fields.
        This is what gets sent over the wire during streaming to reduce payload size.
        
        Returns:
            Dictionary with only streamable fields and their values
        """
        streamable = self.get_streamable_channels()
        result = {}
        
        # Include streamable declared fields
        for field_name in streamable:
            if field_name in self.__class__.model_fields:
                result[field_name] = getattr(self, field_name)
        
        return result

    # —————– Merge Strategy Introspection —————–

    @classmethod
    def get_merge_strategies(cls) -> Dict[str, Callable]:
        """
        Extract the merge function from each Annotated channel field.

        Returns:
            { field_name: merge_callable } for every channel
            that declares a merge strategy via Annotated[Type, fn].
        """
        strategies: Dict[str, Callable] = {}
        hints = get_type_hints(cls, include_extras=True)
        for field_name in cls.model_fields:
            hint = hints.get(field_name)
            if hint and hasattr(hint, '__metadata__'):
                for meta in hint.__metadata__:
                    if callable(meta):
                        strategies[field_name] = meta
                        break
        return strategies

    # —————– Serialization Boundary —————–

    def serialize(self) -> Dict[str, Any]:
        """
        Convert to a JSON-safe dict for cross-process transport.

        Handles types that Pydantic's model_dump() doesn't cover:
          • ChatMessage (dataclass) → dict via dataclasses.asdict
          • BaseIEMPacket (Pydantic with subclasses) → dict via model_dump
          • Everything else → Pydantic default
        """
        from dataclasses import asdict, fields as dc_fields
        from pydantic import BaseModel

        data = {}
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            data[field_name] = _serialize_value(value)

        # Include dynamic_fields
        for key, value in self.dynamic_fields.items():
            data[key] = _serialize_value(value)

        # Remove the raw dynamic_fields dict to avoid duplication
        data.pop("dynamic_fields", None)

        return data

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "GraphState":
        """
        Reconstruct a GraphState from a serialized dict.

        Handles types that Pydantic's model_validate() can't reconstruct
        due to List[Any] or dataclass fields:
          • messages / task_threads → ChatMessage reconstruction
          • inter_packets → BaseIEMPacket reconstruction via discriminator
        """
        from elements.llms.common.chat.message import ChatMessage, Role, ToolCall
        from core.iem.packets import BaseIEMPacket, TaskPacket, SystemPacket, DebugPacket
        from core.iem.models import PacketType

        restored = dict(data)

        # Reconstruct messages: List[ChatMessage] from list of dicts
        if "messages" in restored and isinstance(restored["messages"], list):
            restored["messages"] = [
                _dict_to_chat_message(m) if isinstance(m, dict) else m
                for m in restored["messages"]
            ]

        # Reconstruct task_threads: Dict[str, List[ChatMessage]]
        if "task_threads" in restored and isinstance(restored["task_threads"], dict):
            restored["task_threads"] = {
                tid: [_dict_to_chat_message(m) if isinstance(m, dict) else m for m in msgs]
                for tid, msgs in restored["task_threads"].items()
            }

        # Reconstruct inter_packets: List[BaseIEMPacket] from list of dicts
        _packet_types = {
            PacketType.TASK.value: TaskPacket,
            PacketType.SYSTEM.value: SystemPacket,
            PacketType.DEBUG.value: DebugPacket,
        }
        if "inter_packets" in restored and isinstance(restored["inter_packets"], list):
            packets = []
            for p in restored["inter_packets"]:
                if isinstance(p, dict):
                    ptype = p.get("type", "")
                    packet_cls = _packet_types.get(ptype, BaseIEMPacket)
                    packets.append(packet_cls.model_validate(p))
                else:
                    packets.append(p)
            restored["inter_packets"] = packets

        return cls.model_validate(restored)


# —————– Serialization Helpers —————–

def _serialize_value(value: Any) -> Any:
    """Recursively convert a value to a JSON-safe representation."""
    from dataclasses import asdict, fields as dc_fields
    from pydantic import BaseModel

    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return value.model_dump()
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, set):
        return [_serialize_value(item) for item in value]
    # Fallback — let JSON deal with it
    return value


def _dict_to_chat_message(data: dict) -> "ChatMessage":
    """Reconstruct a ChatMessage dataclass from a plain dict."""
    from elements.llms.common.chat.message import ChatMessage, Role, ToolCall

    role = data.get("role", "assistant")
    if isinstance(role, str):
        role = Role(role)

    tool_calls = None
    if data.get("tool_calls"):
        tool_calls = [
            ToolCall(**tc) if isinstance(tc, dict) else tc
            for tc in data["tool_calls"]
        ]

    return ChatMessage(
        role=role,
        content=data.get("content", ""),
        tool_calls=tool_calls,
        tool_call_id=data.get("tool_call_id"),
        additional_kwargs=data.get("additional_kwargs"),
    )


def _build_channel_enum() -> Enum:
    mapping = {name.upper(): name for name in GraphState.model_fields}
    return Enum("Channel", mapping, type=str)


Channel = _build_channel_enum()
